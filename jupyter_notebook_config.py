import os

port = int(os.environ.get('JUPYTER_NOTEBOOK_PORT', '8080'))

c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = port
c.NotebookApp.open_browser = False


password = os.environ.get('JUPYTER_NOTEBOOK_PASSWORD')
if password:
    import notebook.auth
    c.NotebookApp.password = notebook.auth.passwd(password)
    del password
    del os.environ['JUPYTER_NOTEBOOK_PASSWORD']

image_config_file = '/opt/app-root/src/.jupyter/jupyter_notebook_config.py'

if os.path.exists(image_config_file):
    with open(image_config_file) as fp:
        exec(compile(fp.read(), image_config_file, 'exec'), globals())

 
#######################
# Directories mapping #
#######################
import boto3
from s3contents import S3ContentsManager
from hybridcontents import HybridContentsManager
from notebook.services.contents.filemanager import FileContentsManager

# We use HybridContentsManager (https://github.com/viaduct-ai/hybridcontents),
# FileContentsManager for accessing local volumes
# and S3ContentsManager (https://github.com/danielfrg/s3contents) to connect to the datalake
c.NotebookApp.contents_manager_class = HybridContentsManager

# Intialize Hybrid Contents Manager with local filesystem
c.HybridContentsManager.manager_classes = {
    # Associate the root directory with a FileContentsManager.
    # This manager will receive all requests that don't fall under any of the
    # other managers.
    '': FileContentsManager
}

# Get S3 credentials from environment variables
aws_access_key_id = os.environ.get("accessKeyID")
aws_secret_access_key = os.environ.get("secretAccessKey")
shared_aws_access_key_id = os.environ.get("sharedAccessKeyID")
shared_aws_secret_access_key = os.environ.get("sharedSecretAccessKey")
endpoint_url = os.environ.get("S3_ENDPOINT_URL")

# Add datalake connection information
if (aws_access_key_id and aws_access_key_id!=None): # Make sure we have usable S3 informations are there before configuring
    # Initialize S3 connection (us-east-1 seems to be needed even when it is not used, in Ceph for example)
    s3 = boto3.resource('s3','us-east-2',
                        endpoint_url=endpoint_url,
                        aws_access_key_id = aws_access_key_id,
                        aws_secret_access_key = aws_secret_access_key,
                        use_ssl = True if 'https' in endpoint_url else False ) 
    # Enumerate all accessible buckets and create a folder entry in HybridContentsManager
    for bucket in s3.buckets.all():
        c.HybridContentsManager.manager_classes.update({bucket.name: S3ContentsManager})

# Add datalake connection information for shared S3
if (shared_aws_access_key_id and shared_aws_secret_access_key!=None): # Make sure we have usable S3 informations are there before configuring
    # Initialize S3 connection (us-east-1 seems to be needed even when it is not used, in Ceph for example)
    shared_s3 = boto3.resource('s3','us-east-2',
                        endpoint_url=endpoint_url,
                        aws_access_key_id = shared_aws_access_key_id,
                        aws_secret_access_key = shared_aws_secret_access_key,
                        use_ssl = True if 'https' in endpoint_url else False ) 
    # Enumerate all accessible buckets and create a folder entry in HybridContentsManager
    for bucket in shared_s3.buckets.all():
        c.HybridContentsManager.manager_classes.update({bucket.name: S3ContentsManager})

# Initalize arguments for local filesystem
c.HybridContentsManager.manager_kwargs = {
    # Args for the FileContentsManager mapped to /directory
    '': {
        'root_dir': '/opt/app-root/src'
    }
}

# Add datalake connections arguments
if (aws_access_key_id and aws_access_key_id!=None):
    # We don't have to reinitialize the connection, thanks for previous "for" not being scoped
    # Enumerate all buckets and configure access
    for bucket in s3.buckets.all():
        c.HybridContentsManager.manager_kwargs.update({bucket.name: {
            'access_key_id': aws_access_key_id,
            'secret_access_key': aws_secret_access_key,
            'endpoint_url': endpoint_url,
            'bucket': bucket.name
        } })

# Add datalake connections arguments for Shared S3
if (shared_aws_access_key_id and shared_aws_secret_access_key!=None):
    # We don't have to reinitialize the connection, thanks for previous "for" not being scoped
    # Enumerate all buckets and configure access
    for bucket in shared_s3.buckets.all():
        c.HybridContentsManager.manager_kwargs.update({bucket.name: {
            'access_key_id': shared_aws_access_key_id,
            'secret_access_key': shared_aws_secret_access_key,
            'endpoint_url': endpoint_url,
            'bucket': bucket.name
        } })
