# isaacSim_RealWorld

NVIDIA Isaac Sim ve Cesium Omniverse eklentisi kullanılarak oluşturulmuş gerçek dünya harita ve simülasyon ortamı projesi.

Bu projede Sakarya Üniversitesi Esentepe Kampüsü Cesium 3D Tiles ve Coğrafi Referans (Georeference) kullanılarak modellenmiş USD sahnesi yer almaktadır.

---

## 📁 Proje İçeriği

- **`esentepe_harita.usd`**: Cesium Coğrafi Referanslı (Georeference) Esentepe Kampüsü 3D Tiles haritasını içeren ana Isaac Sim USD sahnesi.
- **`launch.sh`**: Isaac Sim ve Cesium eklentilerini sahne ile birlikte tek komutla başlatan script.

---

## 🚀 Gereksinimler

- **NVIDIA Isaac Sim** (v4.0+ veya v6.0+)
- **Cesium Omniverse Extension** (`cesium.omniverse` ve `cesium.usd.plugins`)
- **NVIDIA GPU** ve güncel sürücüler

---

## ⚙️ Kurulum & Çalıştırma

### 1. Cesium Eklentisinin Hazırlanması

Cesium Omniverse eklentisini Isaac Sim'in kullanıcı eklentileri dizinine (`extsUser`) kopyalayın:

```bash
mkdir -p ~/isaacsim/extsUser
# Cesium eklentilerini extsUser içerisine yerleştirin
# (Gerekirse extension.toml içerisindeki kit sürüm uyumluluğunu güncelleyin)
```

### 2. Sahneyi Başlatma

Projeyi çalıştırmak için scripti kullanabilirsiniz:

```bash
chmod +x launch.sh
./launch.sh
```

Veya doğrudan Isaac Sim dizininden çalıştırmak için:

```bash
cd ~/isaacsim
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia ./isaac-sim.sh \
    --/app/useFabricSceneDelegate=true \
    --enable cesium.usd.plugins \
    --enable cesium.omniverse \
    --open "/yol/to/isaacSim_RealWorld/esentepe_harita.usd"
```
