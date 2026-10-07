#!/bin/bash
# Isaac Sim + Cesium Harita Başlatma Scripti

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USD_PATH="${SCRIPT_DIR}/esentepe_harita.usd"
ISAAC_SIM_PATH="${ISAAC_SIM_PATH:-$HOME/isaacsim}"

if [ ! -d "$ISAAC_SIM_PATH" ]; then
    echo "Hata: Isaac Sim dizini bulunamadı ($ISAAC_SIM_PATH)"
    echo "ISAAC_SIM_PATH ortam değişkenini ayarlayabilirsiniz:"
    echo "  export ISAAC_SIM_PATH=/path/to/isaacsim"
    exit 1
fi

echo "Isaac Sim başlatılıyor..."
echo "USD Sahnesi: $USD_PATH"

cd "$ISAAC_SIM_PATH" || exit 1

__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia ./isaac-sim.sh \
    --/app/useFabricSceneDelegate=true \
    --enable cesium.usd.plugins \
    --enable cesium.omniverse \
    --open "$USD_PATH"
