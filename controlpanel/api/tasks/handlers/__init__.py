from controlpanel import celery_app

from controlpanel.api.tasks.handlers.s3 import (
    CreateS3Bucket, GrantAppS3BucketAccess, GrantUserS3BucketAccess,
)
from controlpanel.api.tasks.handlers.app import CreateAppAuthSettings, CreateAppAWSRole


create_app_aws_role = celery_app.register_task(CreateAppAWSRole())
create_s3bucket = celery_app.register_task(CreateS3Bucket())
grant_app_s3bucket_access = celery_app.register_task(GrantAppS3BucketAccess())
grant_user_s3bucket_access = celery_app.register_task(GrantUserS3BucketAccess())
create_app_auth_settings = celery_app.register_task(CreateAppAuthSettings())