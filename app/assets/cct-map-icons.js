/* Shared CCT map icon factory. Requires Leaflet and the palette below. */
window.CCTMapIcons = (() => {
  const routes = {'305':'#7b2cbf','306':'#e76f51','310':'#2a9d8f','371':'#f4a261','395':'#264653','461':'#d62828','495':'#457b9d','574':'#6a994e','803':'#8338ec','951':'#ff9f1c'};
  const metro = {Blue:'#0072bc',Orange:'#f28c28',Silver:'#8b8f94'};
  const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  return {
    routes, metro,
    bus(routesText){const rs=(routesText||'').split(',').map(x=>x.trim()).filter(Boolean), color=routes[rs[0]]||'#555';return L.divIcon({className:'',html:`<div class="cct-swatch cct-bus" style="background:${color}">${esc(rs.join('/'))}</div>`,iconSize:[38,38],iconAnchor:[19,19]});},
    metro(lines){let line=(lines||'').replace(/Metrorail/ig,'').replace(/Line/ig,'').trim().split(/[,/]/)[0].trim();line=line.charAt(0).toUpperCase()+line.slice(1);const color=metro[line]||'#555';return L.divIcon({className:'',html:`<div class="cct-swatch cct-metro" style="background:${color}"><span>M</span></div>`,iconSize:[30,30],iconAnchor:[15,15]});},
    parking(capacity){return L.divIcon({className:'',html:`<div class="cct-swatch" style="background:${Number(capacity)<=20?'#c62828':'#1565c0'};border-radius:5px;font-size:15px">P</div>`,iconSize:[28,22],iconAnchor:[14,11]});},
    user(){return L.divIcon({className:'',html:'<div class="cct-user-dot"></div>',iconSize:[22,22],iconAnchor:[11,11]})}
  };
})();
