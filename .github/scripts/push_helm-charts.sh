for d in */ ; do
  if [ -f "$d/Chart.yaml" ]; then
    echo "Rendering Helm chart $d to validate defaults..."
    helm package $d
    helm push *.tgz oci://ghcr.io/opentdf/charts
    rm *.tgz
  fi
done