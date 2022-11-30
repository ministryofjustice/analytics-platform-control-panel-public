import structlog
from urllib.parse import urlencode

from controlpanel.api import cluster
from controlpanel.api.models import Tool, ToolDeployment
from controlpanel.frontend.consumers import start_background_task
from controlpanel.oidc import OIDCLoginRequiredMixin
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView
from django.views.generic.list import ListView
from rules.contrib.views import PermissionRequiredMixin
from controlpanel.api.helm import (get_helm_entries, get_chart_version_info, get_default_image_tag_from_helm_chart)

log = structlog.getLogger(__name__)


class ToolList(OIDCLoginRequiredMixin, PermissionRequiredMixin, ListView):
    context_object_name = "tools"
    model = Tool
    permission_required = "api.list_tool"
    template_name = "tool-list.html"

    def get_queryset(self):
        """
        Return a queryset for Tool objects where:

        * The tool is to be run on this version of the infrastructure.

        AND EITHER:

        * The tool is not in beta,

        OR

        * The current user is in the beta tester group for the tool.
        """
        qs = Tool.objects.filter(target_infrastructure=Tool.EKS)
        return qs.filter(
            Q(is_restricted=False) |
            Q(target_users=self.request.user.id)
        )

    def _locate_tool_box_by_chart_name(self, chart_name):
        tool_box = None
        for key, bucket_name in Tool.TOOL_BOX_CHART_LOOKUP.items():
            if key in chart_name:
                tool_box = bucket_name
                break
        return tool_box

    def _find_related_tool_record(self, chart_name, chart_version, image_tag):
        tool_set = Tool.objects.filter(chart_name=chart_name, version=chart_version)
        for item in tool_set:
            if item.image_tag == image_tag:
                return item
        return tool_set.first()

    def _add_new_item_to_tool_box(self, user, tool_box, tool, tools_info, charts_info):
        if tool_box not in tools_info:
            tools_info[tool_box] = {
                "name": tool.name,
                "url": tool.url(user),
                "deployment": None,
                "releases": {},
            }
        image_tag = tool.image_tag
        if not image_tag:
            image_tag = charts_info.get(tool.version, {}).get('image_tag') or 'unknown'
        tool_release_tag = tool.tool_release_tag(image_tag=image_tag)
        if tool_release_tag not in tools_info[tool_box]["releases"]:
            tools_info[tool_box]["releases"][tool_release_tag] = {
                "tool_id": tool.id,
                "chart_name": tool.chart_name,
                "description": charts_info.get(tool.version, {}).get('app_version') or 'Unknown',
                "chart_version": tool.version,
                "image_tag": image_tag
            }

    def _get_tool_deployed_image_tag(self, containers):
        for container in containers:
            if "auth" not in container.name:
                return container.image.split(":")[1]
        return None

    def _add_deployed_charts_info(self, tools_info, user, id_token, charts_info):
        # Get list of deployed tools
        deployments = cluster.ToolDeployment.get_deployments(user, id_token)
        for deployment in deployments:
            chart_name, chart_version = deployment.metadata.labels["chart"].rsplit("-", 1)
            image_tag = self._get_tool_deployed_image_tag(deployment.spec.template.spec.containers)
            tool_box = self._locate_tool_box_by_chart_name(chart_name)
            tool_box = tool_box or 'Unknown'
            tool = self._find_related_tool_record(chart_name, chart_version, image_tag)
            if not tool:
                log.error("this chart({}-{}) has not available from DB. ".format(chart_name, chart_version))
                continue
            self._add_new_item_to_tool_box(user, tool_box, tool, tools_info, charts_info)
            tools_info[tool_box]["deployment"] = {
                "tool_id": tool.id,
                "chart_name": chart_name,
                "chart_version": chart_version,
                "image_tag": image_tag,
                "app_version": charts_info.get(tool.version, {}).get('app_version') or 'Unknown',
                "tool_release_tag": tool.tool_release_tag(image_tag=image_tag),
                "status": ToolDeployment(tool, user).get_status(id_token, deployment=deployment)
            }

    def _retrieve_detail_tool_info(self, user, tools, charts_info):
        tools_info = {}
        for tool in tools:
            # Work out which bucket the chart should be in
            tool_box = self._locate_tool_box_by_chart_name(tool.chart_name)
            # No matching tool bucket for the given chart. So ignore.
            if tool_box:
                self._add_new_item_to_tool_box(user, tool_box, tool, tools_info, charts_info)
        return tools_info

    def _get_charts_info(self, tool_list):
        # Each version now needs to display the chart_name and the
        # "app_version" metadata from helm. TODO: Stop using helm.
        charts_info = {}
        chart_entries = get_helm_entries()
        for tool in tool_list:
            if tool.version in charts_info or tool.image_tag:
                continue

            chart_app_version = get_chart_version_info(chart_entries, tool.chart_name, tool.version)
            image_tag = None
            if chart_app_version:
                image_tag = get_default_image_tag_from_helm_chart(chart_app_version.chart_url, tool.chart_name)
            charts_info[tool.version] ={
                "app_version": chart_app_version.app_version if chart_app_version else 'Unknown',
                "image_tag": image_tag
            }
        return charts_info

    def get_context_data(self, *args, **kwargs):
        """
        Retrieve information about tools and arrange them for the
        template to use them when being rendered.

        The `tool_info` dictionary in the contexts contains information
        about the tools, whether they're deployed for the user,
        versions, etc...arranged by `chart_name`.

        For example:

        ```
        {
           "tools_info": {
               "rstudio": {
                   "name": "RStudio",
                   "url: "https://john-rstudio.tools.example.com",
                   "deployment": {
                       "chart_name": "rstudio",
                       "app_version": "RStudio: 1.2.1335+conda, R: 3.5.1, Python: 3.7.1, patch: 10",
                       "image_tag": "4.0.5",
                       "chart_version": <chart_version>,
                       "tool_id": <id of the tool in table>,
                       "status": <current status of the deployed tool,
                       "tool_release_tag": < from tool.tool_release_tag property>
                   },
                   "releases": {
                       "rstudio-2.2.5-<rstudio image tag>": {
                           "chart_name": "rstudio",
                           "description": "RStudio: 1.2.1335+conda, R: 3.5.1, Python: 3.7.1, patch: 10",
                           "image_tag": "4.0.5",
                           "chart_version": <chart_version>,
                           "tool_id": <id of the tool in table>
                       },
                    }
               },
               # ...
           }
        }
        ```
        """

        user = self.request.user
        id_token = user.get_id_token()

        context = super().get_context_data(*args, **kwargs)
        context["ip_range_feature_enabled"] = settings.features.app_migration.enabled
        context["user_guidance_base_url"] = settings.USER_GUIDANCE_BASE_URL
        context["aws_service_url"] = settings.AWS_SERVICE_URL

        args_airflow_dev_url = urlencode({
        "destination": f"mwaa/home?region={settings.AIRFLOW_REGION}#/environments/dev/sso",
        })
        args_airflow_prod_url = urlencode({
        "destination": f"mwaa/home?region={settings.AIRFLOW_REGION}#/environments/prod/sso",
        })
        context["managed_airflow_dev_url"] = f"{settings.AWS_SERVICE_URL}/?{args_airflow_dev_url}"
        context["managed_airflow_prod_url"] = f"{settings.AWS_SERVICE_URL}/?{args_airflow_prod_url}"

        # Arrange tools information
        charts_info = self._get_charts_info(context["tools"])
        tools_info = self._retrieve_detail_tool_info(user, context["tools"], charts_info)
        self._add_deployed_charts_info(tools_info, user, id_token, charts_info)
        context["tools_info"] = tools_info
        return context


class DeployTool(OIDCLoginRequiredMixin, RedirectView):
    http_method_names = ["post"]
    url = reverse_lazy("list-tools")

    def get_redirect_url(self, *args, **kwargs):
        """
        This is the most backwards thing you'll see for a while. The helm
        task to deploy the tool apparently must happen when the view class
        attempts to redirect to the target url. I'm sure there's a good
        reason why.
        """
        # If there's already a tool deployed, we need to get this from a
        # hidden field posted back in the form. This is used by helm to delete
        # the currently installed chart for the tool before installing the 
        # new chart.
        old_chart_name = self.request.POST.get("deployed_chart_name", None)
        # The selected option from the "version" select control contains the
        # data we need.
        chart_info = self.request.POST["version"]
        # The tool name and version are stored in the selected option's value
        # attribute and then split on "__" to extract them. Why? Because we
        # need both pieces of information to kick off the background helm
        # deploy.
        tool_name, version, tool_id = chart_info.split("__")

        # Kick off the helm chart as a background task.
        start_background_task(
            "tool.deploy",
            {
                "tool_name": tool_name,
                "version": version,
                "tool_id": tool_id,
                "user_id": self.request.user.id,
                "id_token": self.request.user.get_id_token(),
                "old_chart_name": old_chart_name,
            },
        )
        # Tell the user stuff's happening.
        messages.success(
            self.request, f"Deploying {tool_name}... this may take several minutes",
        )
        # Continue the redirect to the target URL (list-tools).
        return super().get_redirect_url(*args, **kwargs)


class RestartTool(OIDCLoginRequiredMixin, RedirectView):
    http_method_names = ["post"]
    url = reverse_lazy("list-tools")

    def get_redirect_url(self, *args, **kwargs):
        """
        So backwards, it's forwards.

        The "name" of the chart to restart is set in the template for
        list-tools, if there's a live deployment.

        That's numberwang.
        """
        name = self.kwargs["name"]

        start_background_task(
            "tool.restart",
            {
                "tool_name": name,
                "tool_id": self.kwargs["tool_id"],
                "user_id": self.request.user.id,
                "id_token": self.request.user.get_id_token(),
            },
        )

        messages.success(
            self.request, f"Restarting {name}...",
        )
        return super().get_redirect_url(*args, **kwargs)
