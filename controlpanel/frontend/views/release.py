from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView
from django.views.generic.edit import DeleteView, UpdateView, CreateView
from django.views.generic.list import ListView
from rules.contrib.views import PermissionRequiredMixin
from django.http.response import HttpResponseRedirect

from controlpanel.api.models import Tool
from controlpanel.frontend.forms import ToolReleaseForm
from controlpanel.oidc import OIDCLoginRequiredMixin


class ReleaseList(OIDCLoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Used to display a list of releases of the tools available in the control
    panel application.
    """
    context_object_name = 'releases'
    model = Tool 
    permission_required = 'api.list_tool_release'
    queryset = Tool.objects.all()
    template_name = "release-list.html"
    ordering = ["name", "version"]


class ReleaseDelete(OIDCLoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Deletes a release for a tool from the control panel application.
    """
    model = Tool 
    permission_required = 'api.destroy_tool_release'

    def get_success_url(self):
        messages.success(self.request, "Successfully deleted release")
        return reverse_lazy("list-tool-releases")


class ReleaseDetail(OIDCLoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Displays and allows editing of a specific release.
    """
    form_class = ToolReleaseForm
    context_object_name = 'release'
    model = Tool
    permission_required = 'api.update_tool_release'
    template_name = "release-detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_users = []
        for user in self.object.target_users.all():
            target_users.append(user.username)
        context['target_users'] = ", ".join(target_users)
        return context

    def form_valid(self, form):
        """
        Ensure the object is updated as expected (for the beta-users).
        """
        self.object = form.save()
        target_list = form.get_target_users()
        if target_list:
            self.object.target_users.set(target_list)
        else:
            self.object.target_users.clear()
        messages.success(self.request, "Successfully updated release")
        return HttpResponseRedirect(reverse_lazy("list-tool-releases"))


class ReleaseCreate(OIDCLoginRequiredMixin,PermissionRequiredMixin,CreateView):
    """
    Create a new release of a tool on the analytic platform.
    """
    form_class = ToolReleaseForm
    context_object_name = 'release'
    model = Tool
    permission_required = "api.create_tool_release"
    template_name = "release-create.html"

    def form_valid(self, form):
        """
        Ensure the object is created as expected (with the beta-users).
        """
        self.object = form.save()
        target_list = form.get_target_users()
        if target_list:
            self.object.target_users.set(target_list)
        # Populate the JSON values needed as arguments for the referenced helm
        # chart to run.
        # These are taken from the most recent valid version of the helm chart
        # (these settings should remain the same across chart versions).
        old_release = (
            # This query is lazy, and starts by matching tools by chart_name...
            Tool.objects.filter(chart_name=self.object.chart_name)
            .exclude(values={})  # ...throw away those with empty values, and,
            .order_by("-created")  # order by latest first, but...
            .first()  # ...get only the first result.
        )
        # Update the values of the new release with those from the old release.
        self.object.values = old_release.values
        self.object.save()
        messages.success(self.request, "Successfully created new release")
        return HttpResponseRedirect(reverse_lazy("list-tool-releases"))
