import docker
import subprocess
import logging

logger = logging.getLogger(__name__)

class DockerService:
    def __init__(self):
        self.client = self._init_client()

    def _init_client(self):
        try:
            # Try using APIClient directly
            client = docker.APIClient(base_url='unix:///var/run/docker.sock')
            client.ping()
            print("Docker client initialized successfully")
            return client
        except Exception as e:
            print(f"Docker client initialization failed: {e}")
            try:
                # Fallback to DockerClient
                client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
                client.ping()
                print("Docker client initialized successfully (fallback)")
                return client
            except Exception as e2:
                print(f"Docker client fallback also failed: {e2}")
                # Try subprocess approach check
                try:
                    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        print("Docker subprocess access available")
                        return "subprocess"
                    else:
                        return None
                except Exception as e3:
                    print(f"Docker subprocess also failed: {e3}")
                    return None

    def get_container(self, container_name: str):
        if not self.client:
            return None
        if self.client == "subprocess":
            # Cannot return container object in subprocess mode
            return "subprocess"
        try:
            if isinstance(self.client, docker.DockerClient):
                return self.client.containers.get(container_name)
            # APIClient returns dict
            return self.client.inspect_container(container_name)
        except Exception:
            return None

docker_service = DockerService()
