let map;
let userMarker;
let shelterMarkers = [];
let AdvancedMarkerElement;

async function initMap() {
  if (!window.google || !window.google.maps) {
    console.warn("Google Maps JS API key is not set. Map will be disabled.");
    return;
  }

  const { Map } = await google.maps.importLibrary("maps");
  const markerLib = await google.maps.importLibrary("marker");
  AdvancedMarkerElement = markerLib.AdvancedMarkerElement;

  const adachi = { lat: 35.7745, lng: 139.8034 };
  map = new Map(document.getElementById("map"), {
    center: adachi,
    zoom: 13,
    mapId: "DEMO_MAP_ID",
  });

  setupEventListeners();
}

function setupEventListeners() {
  document.getElementById("current-location-btn").addEventListener("click", () => {
    if (!navigator.geolocation) {
      alert("位置情報が利用できません");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const loc = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        findAndDisplayShelters(loc);
      },
      () => alert("現在地を取得できませんでした")
    );
  });

  const zipBtn = document.getElementById("zip-search-btn");
  if (zipBtn) {
    zipBtn.addEventListener("click", async () => {
      const zip = (document.getElementById("zip-code").value || "").trim();
      if (!/^\d{7}$/.test(zip)) {
        alert("郵便番号はハイフンなし7桁で入力してください");
        return;
      }
      const url = `${window.API_BASE}/nearest/by-zip?zip=${zip}&limit=5`;
      const res = await fetch(url);
      if (!res.ok) {
        alert("検索に失敗しました");
        return;
      }
      const data = await res.json();
      updateUIFromNearest(data);
    });
  }
}

async function findAndDisplayShelters(userLoc) {
  const url = `${window.API_BASE}/nearest?lat=${userLoc.lat}&lon=${userLoc.lon}&n=5`;
  const res = await fetch(url);
  if (!res.ok) {
    alert("検索に失敗しました");
    return;
  }
  const data = await res.json();
  updateUIFromNearest(data);
}

function updateUIFromNearest(data) {
  const origin = data.origin;
  if (map && origin) {
    map.setCenter({ lat: origin.lat, lng: origin.lon });
    map.setZoom(15);
    if (userMarker) userMarker.map = null;
    userMarker = new AdvancedMarkerElement({
      map,
      position: { lat: origin.lat, lng: origin.lon },
      title: "あなたの現在地",
    });
  }

  const list = document.getElementById("shelter-list");
  list.innerHTML = "";

  shelterMarkers.forEach((m) => (m.map = null));
  shelterMarkers = [];

  (data.items || []).forEach((shelter) => {
    const item = document.createElement("div");
    item.className = "shelter-item";
    const h3 = document.createElement("h3");
    h3.textContent = shelter.name;
    const p = document.createElement("p");
    p.textContent = `距離: ${shelter.distance_km?.toFixed?.(2) ?? "-"} km`;
    item.appendChild(h3);
    item.appendChild(p);

    item.addEventListener("click", () => {
      const destination = `${shelter.lat},${shelter.lon}`;
      const originStr = origin ? `${origin.lat},${origin.lon}` : "";
      const mapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${originStr}&destination=${destination}`;
      window.open(mapsUrl, "_blank");
    });

    list.appendChild(item);

    if (map && AdvancedMarkerElement) {
      const icon = document.createElement("img");
      icon.src = "/static/shelter-icon.png";
      icon.style.width = "48px";
      icon.style.height = "56px";
      icon.style.objectFit = "contain";

      const marker = new AdvancedMarkerElement({
        map,
        position: { lat: shelter.lat, lng: shelter.lon },
        title: shelter.name,
        content: icon,
      });
      shelterMarkers.push(marker);
    }
  });
}

window.initMap = initMap;

