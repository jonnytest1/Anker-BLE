/**
 * Anker BLE Lovelace card — MagGo / Solix style device widget.
 * Uses product art served from /anker_ble_static/images/
 */
class AnkerBleCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("anker-ble-card-editor");
  }

  static getStubConfig(hass, entities) {
    const power = entities.find((e) => e.includes("power_out"));
    const device = power
      ? hass.entities[power]?.device_id
      : undefined;
    return {
      type: "custom:anker-ble-card",
      entity: power || "",
      name: "",
    };
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("Specify an Anker BLE power entity (e.g. sensor.*_power_out)");
    }
    this._config = {
      show_pads: true,
      show_battery: true,
      show_status: true,
      ...config,
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  _state(entityId) {
    if (!entityId || !this._hass) return undefined;
    return this._hass.states[entityId];
  }

  _related(base, suffix) {
    if (!base) return undefined;
    // sensor.foo_power_out → sensor.foo_pad_1_power
    const replaced = base.replace(/_power_out$/, `_${suffix}`);
    if (this._hass?.states[replaced]) return replaced;
    // fallback: same device entities by suffix
    const ent = this._hass?.entities?.[base];
    const deviceId = ent?.device_id;
    if (!deviceId) return undefined;
    for (const [id, meta] of Object.entries(this._hass.entities || {})) {
      if (meta.device_id === deviceId && id.endsWith(`_${suffix}`)) return id;
    }
    return undefined;
  }

  _imageUrl(powerEntity) {
    if (this._config.image) return this._config.image;
    const productId = this._related(powerEntity, "product_name");
    const serialId = this._related(powerEntity, "serial");
    const product = this._state(productId)?.state;
    const serial = this._state(serialId)?.state;
    const imageId = this._related(powerEntity, "device_image");
    const pic = this._state(imageId)?.attributes?.entity_picture;
    if (pic) return pic;

    const blob = `${product || ""} ${serial || ""}`.toLowerCase();
    const map = [
      ["a2687", "a2687.png"],
      ["ashd", "a2687.png"],
      ["a110b", "a110b.png"],
      ["a110g", "a110g.png"],
      ["a110a", "a110a.png"],
      ["a1341", "a1341.png"],
      ["a1340", "a1340.png"],
      ["a1903", "a1903.png"],
      ["a1772", "a1772.png"],
      ["a1771", "a1771.png"],
      ["a1770", "a1770.png"],
      ["charging", "a2687.png"],
      ["160w", "a2687.png"],
      ["prime charger", "a2687.png"],
      ["maggo", "a110a.png"],
      ["solix", "a1770.png"],
    ];
    for (const [hint, file] of map) {
      if (blob.includes(hint)) return `/anker_ble_static/images/${file}`;
    }
    return "/anker_ble_static/images/a2687.png";
  }

  _fmtPower(stateObj) {
    if (!stateObj || stateObj.state === "unavailable" || stateObj.state === "unknown") {
      return "—";
    }
    const n = Number(stateObj.state);
    if (Number.isNaN(n)) return stateObj.state;
    return n >= 10 ? n.toFixed(1) : n.toFixed(2);
  }

  _render() {
    if (!this._config) return;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });

    const powerId = this._config.entity;
    const power = this._state(powerId);
    const name =
      this._config.name ||
      power?.attributes?.friendly_name?.replace(/ Power out$/i, "") ||
      "Anker";
    const onlineId = this._related(powerId, "online");
    const chargingId = this._related(powerId, "charging");
    const batteryId = this._related(powerId, "battery");
    const padIds = ["pad_1_power", "pad_2_power", "pad_3_power"].map((s) =>
      this._related(powerId, s)
    );
    const online = this._state(onlineId);
    const charging = this._state(chargingId);
    const battery = this._state(batteryId);
    const img = this._imageUrl(powerId);
    const onlineOn = online?.state === "on";
    const chargingOn = charging?.state === "on";

    const pads = padIds
      .map((id, i) => {
        const st = this._state(id);
        if (!st || st.state === "unavailable" || st.state === "unknown") return "";
        return `<div class="pad"><span class="pad-label">Port ${i + 1}</span><span class="pad-val">${this._fmtPower(st)}<small>W</small></span></div>`;
      })
      .join("");

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card {
          overflow: hidden;
          background: linear-gradient(165deg, #1a1f24 0%, #0e1114 55%, #12181c 100%);
          color: #f2f5f7;
          border-radius: 20px;
          box-shadow: 0 12px 40px rgba(0,0,0,.35);
          position: relative;
        }
        .glow {
          position: absolute; inset: auto -20% -40% -20%; height: 60%;
          background: radial-gradient(ellipse at center, rgba(0,190,164,.22), transparent 70%);
          pointer-events: none;
        }
        .body {
          display: grid;
          grid-template-columns: 1.05fr 1fr;
          gap: 0.5rem;
          padding: 1.1rem 1.15rem 1rem;
          min-height: 210px;
          position: relative;
          z-index: 1;
        }
        @media (max-width: 450px) {
          .body { grid-template-columns: 1fr; }
          .hero { order: -1; max-height: 160px; }
        }
        .meta { display: flex; flex-direction: column; gap: .55rem; justify-content: center; }
        .brand {
          display: flex; align-items: center; gap: .5rem;
          font-size: .72rem; letter-spacing: .14em; text-transform: uppercase;
          color: #7fd9cb; font-weight: 600;
        }
        .brand img { height: 12px; opacity: .9; }
        .title { font-size: 1.25rem; font-weight: 650; letter-spacing: -.02em; margin: 0; }
        .power {
          font-variant-numeric: tabular-nums;
          font-size: clamp(2.2rem, 6vw, 2.8rem);
          font-weight: 700; line-height: 1; letter-spacing: -.04em;
        }
        .power small { font-size: .4em; margin-left: .15rem; color: #9aa7ae; font-weight: 600; }
        .chips { display: flex; flex-wrap: wrap; gap: .35rem; }
        .chip {
          font-size: .72rem; padding: .28rem .55rem; border-radius: 999px;
          background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.08);
          color: #c5d0d6;
        }
        .chip.on { background: rgba(0,190,164,.18); border-color: rgba(0,190,164,.45); color: #9af0e0; }
        .chip.warn { background: rgba(255,176,32,.12); border-color: rgba(255,176,32,.35); color: #ffd28a; }
        .pads { display: grid; grid-template-columns: repeat(3, 1fr); gap: .4rem; margin-top: .25rem; }
        .pad {
          background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.06);
          border-radius: 12px; padding: .45rem .4rem; text-align: center;
        }
        .pad-label { display: block; font-size: .65rem; color: #8a969d; margin-bottom: .15rem; }
        .pad-val { font-weight: 650; font-variant-numeric: tabular-nums; }
        .pad-val small { color: #8a969d; margin-left: .1rem; font-size: .7em; }
        .hero {
          display: flex; align-items: center; justify-content: center;
          position: relative;
        }
        .hero img {
          max-width: 100%; max-height: 220px; object-fit: contain;
          filter: drop-shadow(0 18px 24px rgba(0,0,0,.45));
          transition: transform .35s ease;
        }
        ha-card:hover .hero img { transform: translateY(-4px) scale(1.02); }
        .foot {
          display: flex; justify-content: space-between; align-items: center;
          padding: 0 1.15rem 0.9rem; color: #7e8a91; font-size: .75rem; position: relative; z-index: 1;
        }
        button.refresh {
          appearance: none; border: 0; background: rgba(255,255,255,.06);
          color: #cfe3df; border-radius: 999px; padding: .35rem .7rem; cursor: pointer; font: inherit;
        }
        button.refresh:hover { background: rgba(0,190,164,.2); }
      </style>
      <ha-card>
        <div class="glow"></div>
        <div class="body">
          <div class="meta">
            <div class="brand">
              <img src="/anker_ble_static/images/anker_solix_logo.svg" alt="" onerror="this.style.display='none'"/>
              Anker BLE
            </div>
            <h2 class="title">${this._esc(name)}</h2>
            <div class="power">${this._fmtPower(power)}<small>W</small></div>
            ${
              this._config.show_status
                ? `<div class="chips">
                    <span class="chip ${onlineOn ? "on" : ""}">${onlineOn ? "Online" : "Offline"}</span>
                    <span class="chip ${chargingOn ? "on" : ""}">${chargingOn ? "Charging" : "Idle"}</span>
                    ${
                      this._config.show_battery && battery && battery.state !== "unavailable" && battery.state !== "unknown"
                        ? `<span class="chip warn">${this._esc(battery.state)}%</span>`
                        : ""
                    }
                   </div>`
                : ""
            }
            ${this._config.show_pads && pads ? `<div class="pads">${pads}</div>` : ""}
          </div>
          <div class="hero">
            <img src="${this._esc(img)}" alt="${this._esc(name)}" />
          </div>
        </div>
        <div class="foot">
          <span>${this._esc(powerId)}</span>
          <button class="refresh" type="button">Refresh</button>
        </div>
      </ha-card>
    `;

    this.shadowRoot.querySelector("button.refresh")?.addEventListener("click", () => {
      if (!this._hass || !powerId) return;
      this._hass.callService("homeassistant", "update_entity", { entity_id: powerId });
    });

    this.shadowRoot.querySelector("ha-card")?.addEventListener("click", (ev) => {
      if (ev.target.closest("button")) return;
      const event = new Event("hass-more-info", { bubbles: true, composed: true });
      event.detail = { entityId: powerId };
      this.dispatchEvent(event);
    });
  }

  _esc(s) {
    return String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll('"', "&quot;");
  }
}

class AnkerBleCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...config };
    this._render();
  }
  set hass(hass) {
    this._hass = hass;
  }
  _render() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <div style="padding:8px 0;display:grid;gap:8px;font-family:var(--ha-font-family-body);">
        <label>Power entity
          <input id="entity" style="width:100%" value="${this._config.entity || ""}" />
        </label>
        <label>Name (optional)
          <input id="name" style="width:100%" value="${this._config.name || ""}" />
        </label>
        <label><input id="pads" type="checkbox" ${this._config.show_pads !== false ? "checked" : ""}/> Show pads</label>
        <label><input id="battery" type="checkbox" ${this._config.show_battery !== false ? "checked" : ""}/> Show battery</label>
      </div>
    `;
    const fire = () => {
      const cfg = {
        ...this._config,
        entity: this.shadowRoot.getElementById("entity").value.trim(),
        name: this.shadowRoot.getElementById("name").value.trim(),
        show_pads: this.shadowRoot.getElementById("pads").checked,
        show_battery: this.shadowRoot.getElementById("battery").checked,
      };
      this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: cfg } }));
    };
    this.shadowRoot.querySelectorAll("input").forEach((el) => el.addEventListener("change", fire));
    this.shadowRoot.querySelectorAll("input").forEach((el) => el.addEventListener("input", fire));
  }
}

customElements.define("anker-ble-card", AnkerBleCard);
customElements.define("anker-ble-card-editor", AnkerBleCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "anker-ble-card",
  name: "Anker BLE Device",
  description: "Anker Prime / MagGo / Solix device card with product art and port power",
  preview: true,
});
