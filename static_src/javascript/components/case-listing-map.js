import L from 'leaflet';

const FALLBACK_COLOR = 'var(--color-m4n-neutral)';
const DEFAULT_CENTER = [54, 15]; // roughly central/northern Europe
const DEFAULT_ZOOM = 4;

class CaseListingMap {
  static selector() {
    return '.case-map';
  }

  constructor(node) {
    this.container = node;
    this.cases = JSON.parse(node.dataset.cases || '[]').filter(
      (c) => typeof c.lat === 'number' && typeof c.lng === 'number'
    );
    this.legend = node.parentElement.querySelector('.case-map-legend');

    this.map = L.map(this.container);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(this.map);

    this.clusterGroup = L.markerClusterGroup({
      iconCreateFunction: (cluster) => L.divIcon({
        className: 'case-map-cluster',
        html: `
          <div class="flex h-10 w-10 items-center justify-center rounded-full border border-grey-600 bg-white">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-grey-800">
              <span class="font-semibold text-white">${cluster.getChildCount()}</span>
            </div>
          </div>
        `,
        iconSize: [40, 40],
      }),
    });
    this.cases.forEach((caseItem) => this.addMarker(caseItem));
    this.map.addLayer(this.clusterGroup);

    if (this.cases.length > 0) {
      this.map.fitBounds(this.clusterGroup.getBounds(), { padding: [24, 24] });
    } else {
      this.map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
    }

    this.renderLegend();
  }

  addMarker(caseItem) {
    const marker = L.marker([caseItem.lat, caseItem.lng], {
      icon: this.buildIcon(caseItem),
    });
    // Tooltip
    marker.bindTooltip(caseItem.title, {
      direction: 'right',
      offset: [24, 0],
      className: 'case-map-tooltip',
      opacity: 1,
    });
    // Clicking a marker goes to the case page
    marker.on('click', () => {
      window.location.href = caseItem.url;
    });
    // Marker hover highlights the matching sidebar card
    marker.on('mouseover', () => this.highlightListItem(caseItem.id, true));
    marker.on('mouseout', () => this.highlightListItem(caseItem.id, false));

    this.clusterGroup.addLayer(marker);
  }

  highlightListItem(caseId, highlighted) {
    const item = document.querySelector(`[data-case-id="${caseId}"]`);
    if (!item) return;

    item.classList.toggle('case-list-item-highlighted', highlighted);
    if (highlighted) {
      item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  buildIcon(caseItem) {
    const color = (caseItem.topic && caseItem.topic.color) || FALLBACK_COLOR;
    return L.divIcon({
      className: 'case-map-marker',
      html: `
        <div class="case-map-pin-inner relative flex h-10 w-10 items-center justify-center transition-transform hover:scale-125">
          <span class="absolute inset-0 rounded-full" style="background-color: ${color};"></span>
          <span class="absolute h-6 w-6 rounded-full border border-grey-800"></span>
          <span class="absolute h-1.5 w-1.5 rounded-full bg-grey-800"></span>
        </div>
      `,
      iconSize: [40, 40],
      iconAnchor: [20, 20],
    });
  }

  renderLegend() {
    if (!this.legend) return;

    const topicsSeen = new Map();
    this.cases.forEach((caseItem) => {
      if (caseItem.topic && caseItem.topic.title && !topicsSeen.has(caseItem.topic.title)) {
        topicsSeen.set(caseItem.topic.title, caseItem.topic.color || FALLBACK_COLOR);
      }
    });

    topicsSeen.forEach((color, title) => {
      const row = document.createElement('div');
      row.className = 'flex items-center gap-2';

      const swatch = document.createElement('span');
      swatch.className = 'inline-block w-3 h-3 rounded-full flex-none';
      swatch.style.backgroundColor = color;

      const label = document.createElement('span');
      label.className = 'font-sans';
      label.textContent = title;

      row.appendChild(swatch);
      row.appendChild(label);
      this.legend.appendChild(row);
    });
  }

}

export default CaseListingMap;
