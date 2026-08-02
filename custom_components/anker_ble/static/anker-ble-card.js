/**
 * Anker BLE Lovelace card — Prime charger / MagGo / Solix device widget.
 * Art: /anker_ble_static/images/
 */
(() => {
  const CARD_VERSION = "0.2.9";
  const DEMO_ENTITY = "sensor.anker_ble_demo_power_out";
  const DEMO = {
    name: "Prime Charger 160W",
    power: "45.2",
    ports: ["20.1", "15.0", "10.1"],
    online: true,
    charging: true,
    battery: null,
    image: "/anker_ble_static/images/a2687.png",
    foot: "sensor.*_power_out",
  };

  function deepMerge(base, extra) {
    return { ...base, ...extra };
  }

  function pickPowerEntity(hass, entities, entitiesFallback) {
    const seen = new Set();
    const list = [];
    for (const e of [...(entities || []), ...(entitiesFallback || []), ...Object.keys(hass?.states || {})]) {
      if (!e || seen.has(e)) continue;
      seen.add(e);
      list.push(e);
    }
    return (
      list.find((e) => /_power_out$/.test(e)) ||
      list.find((e) => /pad_\d_power$/.test(e)) ||
      list.find((e) => e.startsWith("sensor.") && e.includes("anker")) ||
      ""
    );
  }

  class AnkerBleCard extends HTMLElement {
    static getConfigElement() {
      return document.createElement("anker-ble-card-editor");
    }

    static getStubConfig(hass, entities, entitiesFallback) {
      const pick = pickPowerEntity(hass, entities, entitiesFallback);
      return {
        type: "custom:anker-ble-card",
        entity: pick || DEMO_ENTITY,
        name: pick ? "" : DEMO.name,
        show_ports: true,
        show_battery: true,
        show_status: true,
      };
    }

    setConfig(config) {
      // Empty entity is OK — full demo preview is rendered instead of a placeholder.
      this._config = deepMerge(
        {
          entity: "",
          name: "",
          show_ports: true,
          show_pads: true, // legacy alias
          show_battery: true,
          show_status: true,
        },
        config || {}
      );
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

    _deviceId(entityId) {
      return this._hass?.entities?.[entityId]?.device_id;
    }

    /** Map card suffixes → HA unique_id / entity_id endings used by the integration. */
    _suffixCandidates(suffix) {
      const map = {
        power_out: ["power_out", "power_out_w"],
        pad_1_power: ["pad_1_power", "pad_1_power_w"],
        pad_2_power: ["pad_2_power", "pad_2_power_w"],
        pad_3_power: ["pad_3_power", "pad_3_power_w"],
        battery: ["battery", "battery_percent"],
        online: ["online"],
        charging: ["charging"],
        serial: ["serial"],
        firmware: ["firmware"],
        product_name: ["product_name"],
        device_image: ["device_image"],
        telemetry_cmd: ["telemetry_cmd"],
      };
      return map[suffix] || [suffix];
    }

    /** Find another entity on the same device by unique_id / entity_id suffix. */
    _related(base, suffix) {
      if (!base || !this._hass) return undefined;
      const candidates = this._suffixCandidates(suffix);

      for (const c of candidates) {
        const direct = base.replace(/_power_out$/, `_${c}`);
        if (direct !== base && this._hass.states[direct]) return direct;
      }

      const deviceId = this._deviceId(base);
      if (deviceId) {
        for (const [id, meta] of Object.entries(this._hass.entities || {})) {
          if (meta.device_id !== deviceId) continue;
          for (const c of candidates) {
            if (
              id.endsWith(`_${c}`) ||
              id.endsWith(`.${c}`) ||
              (meta.unique_id && String(meta.unique_id).endsWith(`_${c}`))
            ) {
              return id;
            }
          }
        }
      }

      // Fallback: unique_id address prefix (MAC_…) shared with siblings
      const ent = this._hass.entities?.[base];
      const uid = ent?.unique_id && String(ent.unique_id);
      if (uid) {
        // unique_ids are "{mac}_{key}" — mac may contain colons/underscores; match by shared start + candidate end
        for (const [id, meta] of Object.entries(this._hass.entities || {})) {
          const other = meta.unique_id && String(meta.unique_id);
          if (!other) continue;
          for (const c of candidates) {
            if (!other.endsWith(`_${c}`)) continue;
            // Same device if unique_ids share a long common prefix before the last key segment(s)
            const baseStem = uid.replace(/_(?:power_out_w|pad_[123]_power_w|battery_percent|online|charging|serial|firmware|product_name|device_image|telemetry_cmd|power_out|pad_[123]_power|battery)$/, "");
            const otherStem = other.slice(0, other.length - c.length - 1);
            if (baseStem && baseStem === otherStem && this._hass.states[id]) return id;
          }
        }
      }
      return undefined;
    }

    /** Accept power_out or any sibling entity from the Anker BLE device. */
    _resolvePowerEntity(entityId) {
      if (!entityId) return "";
      if (/_power_out$/.test(entityId)) return entityId;
      const power = this._related(entityId, "power_out");
      return power || entityId;
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

      const title = this._config.name || "";
      const blob = `${product || ""} ${serial || ""} ${title} ${powerEntity}`.toLowerCase();
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
        ["prime", "a2687.png"],
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

    _showPorts() {
      if (this._config.show_ports === false) return false;
      if (this._config.show_pads === false && this._config.show_ports == null) return false;
      return true;
    }

    _isDemo(rawEntity, powerId) {
      if (!rawEntity || rawEntity === DEMO_ENTITY) return true;
      if (!this._hass) return true;
      return !this._state(powerId) && !this._state(rawEntity);
    }

    _cardStyles() {
      return `
        :host { display: block; }
        ha-card {
          overflow: hidden;
          position: relative;
          color: var(--primary-text-color);
        }
        .glow {
          position: absolute; inset: auto -20% -45% -20%; height: 55%;
          background: radial-gradient(
            ellipse at center,
            color-mix(in srgb, var(--primary-color) 18%, transparent),
            transparent 70%
          );
          pointer-events: none;
        }
        .body {
          display: grid;
          grid-template-columns: 1.05fr 1fr;
          gap: 0.5rem;
          padding: var(--ha-card-padding, 16px);
          padding-bottom: 12px;
          min-height: 210px;
          position: relative;
          z-index: 1;
        }
        @media (max-width: 450px) {
          .body { grid-template-columns: 1fr; }
          .hero { order: -1; max-height: 160px; }
        }
        .meta {
          display: flex;
          flex-direction: column;
          gap: .55rem;
          justify-content: center;
          min-width: 0;
        }
        .brand {
          display: flex;
          align-items: center;
          gap: .5rem;
          font-size: .72rem;
          letter-spacing: .12em;
          text-transform: uppercase;
          color: var(--primary-color);
          font-weight: var(--ha-font-weight-medium, 500);
        }
        .brand img {
          height: 12px;
          opacity: .85;
          /* Keep logo readable on light and dark themes */
          filter: var(--anker-ble-logo-filter, none);
        }
        .title {
          font-size: 1.25rem;
          font-weight: var(--ha-font-weight-bold, 700);
          letter-spacing: -.02em;
          margin: 0;
          color: var(--primary-text-color);
          overflow-wrap: anywhere;
        }
        .power {
          font-variant-numeric: tabular-nums;
          font-size: clamp(2.2rem, 6vw, 2.8rem);
          font-weight: var(--ha-font-weight-bold, 700);
          line-height: 1;
          letter-spacing: -.04em;
          color: var(--primary-text-color);
        }
        .power small {
          font-size: .4em;
          margin-left: .15rem;
          color: var(--secondary-text-color);
          font-weight: var(--ha-font-weight-medium, 500);
        }
        .chips { display: flex; flex-wrap: wrap; gap: .35rem; }
        .chip {
          font-size: .72rem;
          padding: .28rem .55rem;
          border-radius: var(--ha-border-radius-pill, 999px);
          background: var(--secondary-background-color);
          border: 1px solid var(--divider-color);
          color: var(--secondary-text-color);
        }
        .chip.on {
          background: color-mix(in srgb, var(--success-color, var(--primary-color)) 18%, transparent);
          border-color: color-mix(in srgb, var(--success-color, var(--primary-color)) 45%, transparent);
          color: var(--success-color, var(--primary-color));
        }
        .chip.warn {
          background: color-mix(in srgb, var(--warning-color, var(--accent-color)) 16%, transparent);
          border-color: color-mix(in srgb, var(--warning-color, var(--accent-color)) 40%, transparent);
          color: var(--warning-color, var(--accent-color));
        }
        .pads {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: .4rem;
          margin-top: .25rem;
        }
        .pad {
          background: var(--secondary-background-color);
          border: 1px solid var(--divider-color);
          border-radius: var(--ha-border-radius-md, 12px);
          padding: .45rem .4rem;
          text-align: center;
        }
        .pad-label {
          display: block;
          font-size: .65rem;
          color: var(--secondary-text-color);
          margin-bottom: .15rem;
        }
        .pad-val {
          font-weight: var(--ha-font-weight-bold, 700);
          font-variant-numeric: tabular-nums;
          color: var(--primary-text-color);
        }
        .pad-val small {
          color: var(--secondary-text-color);
          margin-left: .1rem;
          font-size: .7em;
        }
        .hero {
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
        }
        .hero img {
          max-width: 100%;
          max-height: 220px;
          object-fit: contain;
          filter: drop-shadow(0 10px 18px color-mix(in srgb, var(--primary-text-color) 18%, transparent));
          transition: transform .35s ease;
        }
        ha-card:hover .hero img { transform: translateY(-3px) scale(1.02); }
        .foot {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0 var(--ha-card-padding, 16px) 14px;
          color: var(--secondary-text-color);
          font-size: .75rem;
          position: relative;
          z-index: 1;
          gap: .5rem;
          flex-wrap: wrap;
          border-top: 1px solid var(--divider-color);
          margin-top: 2px;
          padding-top: 10px;
        }
        button.refresh {
          appearance: none;
          border: 1px solid var(--divider-color);
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
          border-radius: var(--ha-border-radius-pill, 999px);
          padding: .35rem .7rem;
          cursor: pointer;
          font: inherit;
        }
        button.refresh:hover {
          border-color: var(--primary-color);
          color: var(--primary-color);
        }
        button.refresh:disabled {
          opacity: .55;
          cursor: default;
        }
        button.refresh:disabled:hover {
          border-color: var(--divider-color);
          color: var(--primary-text-color);
        }
      `;
    }

    _render() {
      if (!this._config) return;
      if (!this.shadowRoot) this.attachShadow({ mode: "open" });

      const rawEntity = (this._config.entity || "").trim();
      const powerId = this._resolvePowerEntity(rawEntity);
      const demo = this._isDemo(rawEntity, powerId);

      let name;
      let powerText;
      let onlineOn;
      let chargingOn;
      let batteryText = null;
      let img;
      let foot;
      let padIds = [];
      let portsHtml;

      if (demo) {
        name = this._config.name || DEMO.name;
        powerText = DEMO.power;
        onlineOn = DEMO.online;
        chargingOn = DEMO.charging;
        batteryText =
          this._config.show_battery !== false && DEMO.battery != null
            ? String(DEMO.battery)
            : null;
        img = this._config.image || DEMO.image;
        foot = rawEntity && rawEntity !== DEMO_ENTITY ? rawEntity : DEMO.foot;
        portsHtml = DEMO.ports
          .map(
            (val, i) =>
              `<div class="pad"><span class="pad-label">Port ${i + 1}</span><span class="pad-val">${val}<small>W</small></span></div>`
          )
          .join("");
      } else {
        const power = this._state(powerId);
        name =
          this._config.name ||
          power?.attributes?.friendly_name?.replace(/\s+Power out$/i, "") ||
          this._state(this._related(powerId, "product_name"))?.state ||
          "Anker";
        const onlineId = this._related(powerId, "online") || this._related(rawEntity, "online");
        const chargingId =
          this._related(powerId, "charging") || this._related(rawEntity, "charging");
        const batteryId =
          this._related(powerId, "battery") || this._related(rawEntity, "battery");
        padIds = ["pad_1_power", "pad_2_power", "pad_3_power"].map(
          (s) => this._related(powerId, s) || this._related(rawEntity, s)
        );
        const online = this._state(onlineId);
        const charging = this._state(chargingId);
        const battery = this._state(batteryId);
        img = this._imageUrl(powerId || rawEntity);
        onlineOn = online?.state === "on";
        chargingOn = charging?.state === "on";
        powerText = this._fmtPower(power);
        if (
          this._config.show_battery !== false &&
          battery &&
          battery.state !== "unavailable" &&
          battery.state !== "unknown"
        ) {
          batteryText = String(battery.state);
        }
        foot = powerId || rawEntity;
        portsHtml = padIds
          .map((id, i) => {
            const st = this._state(id);
            const val = st ? this._fmtPower(st) : "—";
            return `<div class="pad"><span class="pad-label">Port ${i + 1}</span><span class="pad-val">${val}<small>W</small></span></div>`;
          })
          .join("");
      }

      this.shadowRoot.innerHTML = `
      <style>${this._cardStyles()}</style>
      <ha-card>
        <div class="glow"></div>
        <div class="body">
          <div class="meta">
            <div class="brand">
              <img src="/anker_ble_static/images/anker_solix_logo.svg" alt="" onerror="this.style.display='none'"/>
              Anker BLE
            </div>
            <h2 class="title">${this._esc(name)}</h2>
            <div class="power">${this._esc(powerText)}<small>W</small></div>
            ${
              this._config.show_status !== false
                ? `<div class="chips">
                    <span class="chip ${onlineOn ? "on" : ""}">${onlineOn ? "Online" : "Offline"}</span>
                    <span class="chip ${chargingOn ? "on" : ""}">${chargingOn ? "Charging" : "Idle"}</span>
                    ${
                      batteryText != null
                        ? `<span class="chip warn">${this._esc(batteryText)}%</span>`
                        : ""
                    }
                   </div>`
                : ""
            }
            ${this._showPorts() ? `<div class="pads">${portsHtml}</div>` : ""}
          </div>
          <div class="hero">
            <img src="${this._esc(img)}" alt="${this._esc(name)}" />
          </div>
        </div>
        <div class="foot">
          <span>${this._esc(foot)}</span>
          <button class="refresh" type="button"${demo ? " disabled" : ""}>Refresh</button>
        </div>
      </ha-card>
    `;

      this.shadowRoot.querySelector("button.refresh")?.addEventListener("click", (ev) => {
        ev.stopPropagation();
        if (demo || !this._hass) return;
        const targets = [powerId, rawEntity, ...padIds].filter(Boolean);
        if (!targets.length) return;
        this._hass.callService("homeassistant", "update_entity", {
          entity_id: targets,
        });
      });

      this.shadowRoot.querySelector("ha-card")?.addEventListener("click", (ev) => {
        if (ev.target.closest("button")) return;
        if (demo) return;
        const event = new Event("hass-more-info", { bubbles: true, composed: true });
        event.detail = { entityId: powerId || rawEntity };
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
      this._config = deepMerge(
        {
          entity: "",
          name: "",
          show_ports: true,
          show_battery: true,
          show_status: true,
        },
        config || {}
      );
      // Prefer show_ports; mirror legacy show_pads
      if (config && config.show_pads != null && config.show_ports == null) {
        this._config.show_ports = config.show_pads;
      }
      // Do NOT remount here — Lovelace echoes config after every keystroke/Enter
      // and rebuilding ha-form steals focus from the Name field.
      if (!this._form && this._hass) {
        this._render();
      }
    }

    set hass(hass) {
      this._hass = hass;
      if (this._form) {
        this._form.hass = hass;
        return;
      }
      if (this._config) {
        this._render();
      }
    }

    connectedCallback() {
      if (!this._boundKeyDown) {
        this._boundKeyDown = (ev) => {
          // Enter must not submit the dashboard editor dialog / remount the form.
          if (ev.key === "Enter") {
            ev.preventDefault();
            ev.stopPropagation();
          }
        };
      }
      this.addEventListener("keydown", this._boundKeyDown);
    }

    disconnectedCallback() {
      if (this._boundKeyDown) {
        this.removeEventListener("keydown", this._boundKeyDown);
      }
    }

    _schema() {
      return [
        {
          name: "entity",
          selector: {
            entity: {
              // Power out + Port 1–3 from this integration only.
              filter: [
                {
                  integration: "anker_ble",
                  domain: "sensor",
                  device_class: "power",
                },
              ],
            },
          },
        },
        { name: "name", selector: { text: {} } },
        {
          name: "show_ports",
          selector: { boolean: {} },
        },
        {
          name: "show_battery",
          selector: { boolean: {} },
        },
        {
          name: "show_status",
          selector: { boolean: {} },
        },
      ];
    }

    _label(schema) {
      const labels = {
        entity: "Power out sensor",
        name: "Name (optional)",
        show_ports: "Show Port 1–3",
        show_battery: "Show battery",
        show_status: "Show status chips",
      };
      return labels[schema.name] || schema.name;
    }

    _render() {
      if (!this._config || this._form || this._fallback) return;
      if (!this._hass) return;
      // Use light DOM so ha-form / entity picker work (broken inside shadow roots).
      this.innerHTML = `
        <div class="anker-ble-editor" style="padding:4px 0 8px">
          <div style="color:var(--secondary-text-color);font-size:.85rem;margin:.35rem 0 .75rem;line-height:1.35">
            Select <strong>Power out</strong> (<code>sensor.*_power_out</code>) for your Anker BLE device.
            Port power sensors also work.
          </div>
          <div id="anker-ble-form-host"></div>
        </div>
      `;

      const host = this.querySelector("#anker-ble-form-host");
      if (!host) return;

      try {
        const form = document.createElement("ha-form");
        form.hass = this._hass;
        form.data = {
          entity: this._config.entity || "",
          name: this._config.name || "",
          show_ports: this._config.show_ports !== false,
          show_battery: this._config.show_battery !== false,
          show_status: this._config.show_status !== false,
        };
        form.schema = this._schema();
        form.computeLabel = (schema) => this._label(schema);
        form.addEventListener("value-changed", (ev) => {
          const value = ev.detail?.value || {};
          const next = {
            type: this._config.type || "custom:anker-ble-card",
            ...this._config,
            ...value,
            show_pads: value.show_ports !== false,
          };
          this._config = next;
          this.dispatchEvent(
            new CustomEvent("config-changed", { detail: { config: next } })
          );
        });
        this._form = form;
        host.appendChild(form);
      } catch (err) {
        this._fallback = true;
        host.innerHTML = `
          <div style="display:grid;gap:10px">
            <label>Power out sensor
              <input id="entity" type="text" style="width:100%" placeholder="sensor.xxx_power_out"
                value="${this._esc(this._config.entity || "")}" />
            </label>
            <label>Name (optional)
              <input id="name" type="text" style="width:100%" value="${this._esc(this._config.name || "")}" />
            </label>
            <label><input id="ports" type="checkbox" ${this._config.show_ports !== false ? "checked" : ""}/> Show Port 1–3</label>
            <label><input id="battery" type="checkbox" ${this._config.show_battery !== false ? "checked" : ""}/> Show battery</label>
            <label><input id="status" type="checkbox" ${this._config.show_status !== false ? "checked" : ""}/> Show status chips</label>
          </div>
        `;
        const fire = () => {
          const next = {
            type: this._config.type || "custom:anker-ble-card",
            ...this._config,
            entity: host.querySelector("#entity").value.trim(),
            name: host.querySelector("#name").value.trim(),
            show_ports: host.querySelector("#ports").checked,
            show_battery: host.querySelector("#battery").checked,
            show_status: host.querySelector("#status").checked,
          };
          next.show_pads = next.show_ports;
          this._config = next;
          this.dispatchEvent(
            new CustomEvent("config-changed", { detail: { config: next } })
          );
        };
        host.querySelectorAll("input").forEach((el) => {
          el.addEventListener("change", fire);
          el.addEventListener("input", fire);
        });
      }
    }

    _esc(s) {
      return String(s ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll('"', "&quot;");
    }
  }

  if (!customElements.get("anker-ble-card")) {
    customElements.define("anker-ble-card", AnkerBleCard);
  }
  if (!customElements.get("anker-ble-card-editor")) {
    customElements.define("anker-ble-card-editor", AnkerBleCardEditor);
  }

  window.customCards = window.customCards || [];
  if (!window.customCards.some((c) => c.type === "anker-ble-card")) {
    window.customCards.push({
      type: "anker-ble-card",
      name: "Anker BLE Device",
      description:
        "Prime charger / MagGo / Solix card with product art and USB-C port power",
      preview: true,
      documentationURL: "https://github.com/T-REX-XP/Anker-BLE/blob/main/custom_components/anker_ble/lovelace.md",
    });
  }

  console.info(
    `%c Anker BLE Card %c ${CARD_VERSION} `,
    "background:#00bea4;color:#062016;font-weight:700;padding:2px 6px;border-radius:4px 0 0 4px",
    "background:#1a1f24;color:#9af0e0;padding:2px 6px;border-radius:0 4px 4px 0"
  );
})();
