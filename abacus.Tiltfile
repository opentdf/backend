load("ext://helm_resource", "helm_resource", "helm_repo")
load("./common.Tiltfile", "backend")

EXTERNAL_URL = "http://localhost:65432"
FRONTEND_IMAGE_TAG = "main"
FRONTEND_CHART_TAG = "0.0.0-sha-93bb332"

#backend(extra_helm_parameters=["-f", "./tests/integration/backend-with-frontend.yaml"])
#docker_build(
#        "opentdf/abacus",
#        "../frontend"
        # dockerfile="../frontend/DockerfileTests"
#)
#CONTAINER_REGISTRY = os.environ.get("CONTAINER_REGISTRY", "ghcr.io")
#docker_build(CONTAINER_REGISTRY + "/opentdf/frontend")
# k8s_yaml("./tests/integration/frontend-local.yaml")

def frontend():
  CONTAINER_REGISTRY = os.environ.get("CONTAINER_REGISTRY", "ghcr.io")
  FRONTEND_DIR = "/Users/mustyantsev/temp/abacus/frontend" #os.getcwd()
  docker_build(
        CONTAINER_REGISTRY + "/opentdf/abacus",
        context=FRONTEND_DIR,
  )

  helm_resource(
    name="opentdf-abacus",
    chart=FRONTEND_DIR + "/charts/abacus",
    image_deps=[
                CONTAINER_REGISTRY + "/opentdf/abacus"],
    image_keys=[
                ("ghcr.io/opentdf/abacus", "sha-3e6ac9e")],
    labels="frontend",
    #resource_deps=["backend"],
)