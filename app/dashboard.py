"""Self-contained local weather dashboard served by the API."""

DASHBOARD_HTML = r"""<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>Sky Weather Outpost</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:#14231f;background:#f3f6f2;font-synthesis:none;text-rendering:optimizeLegibility;--muted:#718079;--line:#e4eae5;--green:#26785f;--green-soft:#e6f2eb;--blue:#5b82a8;--panel:#fff;--shadow:0 12px 36px #173b2810}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 84% 0%,#e4f0e7 0,transparent 33rem),#f3f6f2}
button{font:inherit}.shell{max-width:1220px;margin:auto;padding:34px 28px 48px}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:38px}
.brand{display:flex;align-items:center;gap:11px;font-weight:750;letter-spacing:.08em;font-size:13px;color:#37584a}
.brand-mark{width:34px;height:34px;border-radius:11px;background:#1f654e;color:white;display:grid;place-items:center}
.brand-mark svg{width:22px;height:22px}.live{display:flex;align-items:center;gap:8px;color:#66766e;font-size:13px}
.pulse{width:8px;height:8px;background:#45a77c;border-radius:50%;box-shadow:0 0 0 4px #45a77c20}
.heading{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;margin-bottom:26px}
.eyebrow{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--green);font-weight:750;margin:0 0 9px}
h1{font-size:clamp(30px,4vw,43px);letter-spacing:-.045em;margin:0;font-weight:720;line-height:1.05}
.subtitle{color:var(--muted);margin:10px 0 0;font-size:15px}
.periods{display:flex;gap:4px;background:#e8ede8;border:1px solid #dfe7e0;padding:4px;border-radius:13px;flex-shrink:0}
.periods button{border:0;border-radius:9px;padding:9px 14px;color:#66756d;background:transparent;cursor:pointer;font-size:13px;font-weight:650;transition:.15s}
.periods button:hover{color:#183d30}.periods button[aria-pressed=true]{background:#fff;color:#205b47;box-shadow:0 2px 7px #183d3018}
.notice{display:none;margin:0 0 18px;padding:12px 15px;border-radius:12px;background:#fff3e9;color:#87552e;font-size:14px}
.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-bottom:18px}
.card,.panel{background:var(--panel);border:1px solid #e6ece6;border-radius:18px;box-shadow:var(--shadow)}
.card{padding:20px 22px;min-height:126px;position:relative;overflow:hidden}
.card:after{content:"";position:absolute;width:110px;height:110px;border-radius:50%;right:-33px;top:-34px;background:var(--green-soft)}
.card.humidity:after{background:#eaf0f7}
.card-label{position:relative;z-index:1;color:#65756d;font-size:13px;font-weight:630}
.card-value{position:relative;z-index:1;margin-top:11px;font-size:34px;font-weight:730;letter-spacing:-.05em}
.card-value small{font-size:18px;letter-spacing:0;font-weight:600;color:#53645b;margin-left:3px}
.card-foot{position:relative;z-index:1;margin-top:5px;color:#91a097;font-size:12px}
.panel{padding:20px 22px 16px;margin-bottom:16px}
.panel-head{display:flex;align-items:center;justify-content:space-between;gap:12px}
.panel-title{margin:0;font-size:16px;font-weight:700;letter-spacing:-.015em}
.legend{font-size:12px;color:#839088;display:flex;align-items:center;gap:7px}
.legend i{display:inline-block;width:19px;height:3px;background:var(--green);border-radius:3px}
.graph{height:250px;margin-top:9px;position:relative}
.graph svg{width:100%;height:100%;overflow:visible}
.gridline{stroke:#e9eeea;stroke-width:1}.axis-label{fill:#89968f;font-size:11px;font-family:inherit}.midnight-line{stroke:#aab9b0;stroke-width:1;stroke-dasharray:4 4}
.zero-line{stroke:#76867d;stroke-width:1.5;stroke-dasharray:6 5}.range{fill:#dceee4;opacity:.8}.range-bar{stroke:#dceee4;stroke-width:6;stroke-linecap:round}.line{fill:none;stroke:var(--green);stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round}
.dot{fill:#fff;stroke:var(--green);stroke-width:2}.empty{height:100%;display:grid;place-items:center;color:#96a29b;font-size:14px}
.footer{display:flex;justify-content:space-between;gap:12px;color:#8a9790;font-size:12px;padding:10px 3px}
.footer strong{color:#65756d;font-weight:600}.data-status{color:#65756d}
@media(max-width:700px){.shell{padding:22px 15px 34px}.topbar{margin-bottom:29px}.heading{display:block}.periods{width:max-content;margin-top:20px;max-width:100%}.periods button{padding:9px 11px}.cards{gap:10px}.card{padding:17px 15px;min-height:118px}.card-value{font-size:30px}.panel{padding:17px 14px 12px}.graph{height:220px}.footer{display:block;line-height:1.8}}
@media(max-width:390px){.periods{gap:0}.periods button{padding:8px 9px;font-size:12px}.card-foot{font-size:11px}}
</style>
</head>
<body>
<main class="shell">
  <header class="topbar">
    <div class="brand">
      <span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none"><path d="M4 16.5c2.5-5 5-5 7.5 0s5 5 8.5-2M5 9.5c2-3 4-3 6 0s4 3 7 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></span>
      <span>SKY WEATHER OUTPOST</span>
    </div>
    <div class="live"><span class="pulse"></span><span>lokalne pomiary</span></div>
  </header>

  <section class="heading">
    <div>
      <p class="eyebrow" id="siteLabel">Stacja pogodowa</p>
      <h1>Historia pogody</h1>
      <p class="subtitle"><span id="nodeLabel">Węzeł</span> · <span id="rangeLabel">Temperatura i wilgotność w czasie</span></p>
    </div>
    <nav class="periods" aria-label="Zakres historii">
      <button type="button" data-period="day" aria-pressed="true">Dzień</button>
      <button type="button" data-period="week" aria-pressed="false">Tydzień</button>
      <button type="button" data-period="month" aria-pressed="false">Miesiąc</button>
      <button type="button" data-period="year" aria-pressed="false">Rok</button>
    </nav>
  </section>

  <div class="notice" id="notice" role="status"></div>

  <section class="cards" aria-label="Najnowszy odczyt">
    <article class="card">
      <div class="card-label">Temperatura</div>
      <div class="card-value" id="temperatureNow">—<small>°C</small></div>
      <div class="card-foot" id="temperatureAt">Oczekiwanie na dane</div>
    </article>
    <article class="card humidity">
      <div class="card-label">Wilgotność</div>
      <div class="card-value" id="humidityNow">—<small>%</small></div>
      <div class="card-foot" id="humidityAt">Oczekiwanie na dane</div>
    </article>
  </section>

  <section class="panel">
    <div class="panel-head">
      <h2 class="panel-title">Temperatura</h2>
      <span class="legend"><i></i> średnia <span>·</span> zakres min–max</span>
    </div>
    <div class="graph" id="temperatureChart" aria-label="Wykres temperatury"></div>
  </section>

  <section class="panel">
    <div class="panel-head">
      <h2 class="panel-title">Wilgotność</h2>
      <span class="legend"><i style="background:var(--blue)"></i> średnia <span>·</span> zakres min–max</span>
    </div>
    <div class="graph" id="humidityChart" aria-label="Wykres wilgotności"></div>
  </section>

  <footer class="footer">
    <span id="sensorLabel">Czujnik —</span>
    <span id="dataStatus">Ostatni pomiar: —</span>
    <span>Ostatnia aktualizacja: <strong id="updatedAt">—</strong></span>
  </footer>
</main>
<script>
(() => {
  const periodLabels = {day:"ostatnie 24 godziny",week:"ostatnie 7 dni",month:"ostatnie 30 dni",year:"ostatnie 365 dni"};
  let period = "day";
  let timezone = "Europe/Warsaw";
  let currentData = null;
  let historyData = null;
  let resizeTimer;

  const $ = (id) => document.getElementById(id);
  const number = (value) => new Intl.NumberFormat("pl-PL", {maximumFractionDigits:1}).format(value);
  const dateTime = (value, options) => new Intl.DateTimeFormat("pl-PL", {timeZone:timezone,...options}).format(new Date(value));

  document.querySelectorAll("[data-period]").forEach((button) => {
    button.addEventListener("click", () => {
      period = button.dataset.period;
      document.querySelectorAll("[data-period]").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
      load();
    });
  });

  function latestWeather(payload) {
    const device = (payload.devices || []).find((item) => item.type === "weather_sensor");
    if (!device) {
      $("temperatureNow").innerHTML = "—<small>°C</small>";
      $("humidityNow").innerHTML = "—<small>%</small>";
      $("temperatureAt").textContent = "Brak odebranego odczytu";
      $("humidityAt").textContent = "Brak odebranego odczytu";
      $("sensorLabel").textContent = "Brak skonfigurowanego czujnika";
      return;
    }
    const measurements = device.measurements || {};
    const at = device.measured_at || device.received_at;
    const when = at ? dateTime(at,{hour:"2-digit",minute:"2-digit",day:"2-digit",month:"2-digit"}) : "—";
    const temperature = measurements.temperature;
    const humidity = measurements.humidity;
    $("temperatureNow").innerHTML = temperature ? number(temperature.value) + "<small>°C</small>" : "—";
    $("humidityNow").innerHTML = humidity ? number(humidity.value) + "<small>%</small>" : "—";
    $("temperatureAt").textContent = "Pomiar: " + when;
    $("humidityAt").textContent = "Pomiar: " + when;
    $("sensorLabel").textContent = "Czujnik: " + device.name;
  }

  function updateDataStatus(device, historyDevice, history) {
    const status=$("dataStatus");
    const latest=device&&(device.measured_at||device.received_at);
    if(!latest){
      status.textContent="Ostatni pomiar: brak";
      return;
    }
    const latestTime=Date.parse(latest);
    const age=Math.max(0,Date.now()-latestTime);
    const ageLabel=age<60000?"przed chwilą":age<3600000?Math.floor(age/60000)+" min temu":age<86400000?Math.floor(age/3600000)+" godz. temu":Math.floor(age/86400000)+" dni temu";
    const latestLabel=dateTime(latest,{hour:"2-digit",minute:"2-digit",day:"2-digit",month:"2-digit"});
    const points=(historyDevice&&historyDevice.points||[]).map((point)=>Date.parse(point.at)).filter(Number.isFinite).sort((a,b)=>a-b);
    const bucketMilliseconds=(Number(history.bucket_seconds)||0)*1000;
    let missingBuckets=0;
    if(bucketMilliseconds>0){
      for(let index=1;index<points.length;index++){
        const bucketGap=(points[index]-points[index-1])/bucketMilliseconds;
        if(bucketGap>1.5) missingBuckets+=Math.max(1,Math.round(bucketGap)-1);
      }
    }
    const coverageLabel=points.length
      ? "Brakujące przedziały: "+missingBuckets
      : "Brak pomiarów w tym okresie";
    status.textContent="Ostatni pomiar: "+latestLabel+" ("+ageLabel+") · "+coverageLabel;
  }

  function chart(container, points, metric, unit, bucketSeconds) {
    const usable = points.map((point) => {
      const item = point.measurements && point.measurements[metric];
      return item ? {at:point.at,timestamp:Date.parse(point.at),average:Number(item.average),min:Number(item.min),max:Number(item.max),samples:item.samples} : null;
    }).filter(Boolean);
    if (!usable.length) {
      container.innerHTML = '<div class="empty">Brak pomiarów w tym zakresie</div>';
      return;
    }

    const width = Math.max(320, Math.round(container.clientWidth || 800));
    const height = Math.max(200, Math.round(container.clientHeight || 250));
    const left=54,right=16,top=14,bottom=34,plotW=width-left-right,plotH=height-top-bottom;
    let low=Math.min(...usable.map((item)=>item.min));
    let high=Math.max(...usable.map((item)=>item.max));
    const niceStep=(raw)=>{
      const magnitude=Math.pow(10,Math.floor(Math.log10(raw)));
      const fraction=raw/magnitude;
      const nice=fraction<=1.5?1:fraction<=2.25?2:fraction<=3.75?2.5:fraction<=7.5?5:10;
      return nice*magnitude;
    };
    const yTicks=[];
    if(metric==="temperature"){
      const extent=Math.max(Math.abs(low),Math.abs(high),0.5);
      const step=niceStep(extent/3);
      const segments=Math.ceil(extent/step);
      low=-segments*step; high=segments*step;
      for(let index=-segments;index<=segments;index++) yTicks.push(Number((index*step).toFixed(2)));
    }else{
      if(low===high){low-=1;high+=1;}
      const step=niceStep((high-low)/6);
      low=Math.floor(low/step)*step; high=Math.ceil(high/step)*step;
      for(let value=low;value<=high+step*0.001;value+=step) yTicks.push(Number(value.toFixed(2)));
    }
    const historyRange=historyData||{};
    const requestedStart=Date.parse(historyRange.from||"");
    const requestedEnd=Date.parse(historyRange.to||"");
    const firstTimestamp=Number.isFinite(requestedStart)?requestedStart:Date.parse(usable[0].at);
    const lastTimestamp=Number.isFinite(requestedEnd)?requestedEnd:Date.parse(usable[usable.length-1].at);
    const xAt=(timestamp)=>left+(lastTimestamp===firstTimestamp?plotW/2:(timestamp-firstTimestamp)*plotW/(lastTimestamp-firstTimestamp));
    const x=(index)=>xAt(usable[index].timestamp);
    const y=(value)=>top+(high-value)*plotH/(high-low);
    const boundaryXs=[];
    const monthBoundaries=[];
    const calendarFormatter=new Intl.DateTimeFormat("en-GB",{timeZone:timezone,year:"numeric",month:"2-digit",day:"2-digit",weekday:"short",hour:"2-digit",minute:"2-digit",hourCycle:"h23"});
    for(let timestamp=Math.ceil(firstTimestamp/3600000)*3600000;timestamp<=lastTimestamp;timestamp+=3600000){
      const parts=Object.fromEntries(calendarFormatter.formatToParts(new Date(timestamp)).map((part)=>[part.type,part.value]));
      if(parts.hour!=="00"||parts.minute!=="00") continue;
      const isMonthStart=parts.day==="01";
      const isBoundary=period==="day"
        ||(period==="week"&&parts.weekday==="Mon")
        ||(period==="month"&&isMonthStart)
        ||(period==="year"&&isMonthStart&&parts.month==="01");
      if(isBoundary) boundaryXs.push(xAt(timestamp));
      if(period==="year"&&isMonthStart) monthBoundaries.push(timestamp);
    }

    const ns="http://www.w3.org/2000/svg";
    const svg=document.createElementNS(ns,"svg");
    svg.setAttribute("viewBox","0 0 "+width+" "+height);
    svg.setAttribute("role","img");
    svg.setAttribute("aria-label",(metric==="temperature"?"Temperatura":"Wilgotność")+" w okresie "+periodLabels[period]);

    function element(tag,attrs,text) {
      const node=document.createElementNS(ns,tag);
      Object.entries(attrs||{}).forEach(([key,value])=>node.setAttribute(key,String(value)));
      if(text!==undefined) node.textContent=text;
      svg.appendChild(node);
      return node;
    }
    yTicks.forEach((value)=>{
      const yy=y(value);
      element("line",{x1:left,y1:yy,x2:width-right,y2:yy,class:"gridline"});
      element("text",{x:left-9,y:yy+4,"text-anchor":"end",class:"axis-label"},number(value)+unit);
    });
    const maxGapMilliseconds=Math.max(1,Number(bucketSeconds)||0)*1500;
    const segments=[];
    usable.forEach((item,index)=>{
      const previous=usable[index-1];
      if(!previous||item.timestamp-previous.timestamp>maxGapMilliseconds) segments.push([]);
      segments[segments.length-1].push({item,index});
    });
    segments.forEach((segment)=>{
      if(segment.length===1){
        const {item,index}=segment[0];
        if(item.max>item.min) element("line",{x1:x(index),y1:y(item.max),x2:x(index),y2:y(item.min),class:"range-bar"});
        return;
      }
      const upper=segment.map(({item,index})=>x(index)+","+y(item.max));
      const lower=segment.map(({item,index})=>x(index)+","+y(item.min)).reverse();
      element("polygon",{points:upper.concat(lower).join(" "),class:"range"});
    });
    boundaryXs.forEach((xx)=>element("line",{x1:xx,y1:top,x2:xx,y2:top+plotH,class:"midnight-line"}));
    if(metric==="temperature"){
      element("line",{x1:left,y1:y(0),x2:width-right,y2:y(0),class:"zero-line"});
    }
    segments.forEach((segment)=>{
      const line=segment.map(({item,index},segmentIndex)=>(segmentIndex?"L":"M")+" "+x(index)+" "+y(item.average)).join(" ");
      element("path",{d:line,class:"line",stroke:metric==="humidity"?"#5b82a8":"#26785f"});
    });
    let timeLabels;
    if(period==="day"){
      const hourFormatter=new Intl.DateTimeFormat("en-GB",{timeZone:timezone,hour:"2-digit",minute:"2-digit",hourCycle:"h23"});
      const fullHourLabels=[];
      for(let timestamp=Math.ceil(firstTimestamp/3600000)*3600000;timestamp<=lastTimestamp;timestamp+=3600000){
        const parts=hourFormatter.formatToParts(new Date(timestamp));
        const hour=Number(parts.find((part)=>part.type==="hour").value);
        const minute=parts.find((part)=>part.type==="minute").value;
        if(minute==="00"&&hour%2===0){
          const label=hourFormatter.format(new Date(timestamp)).replace(":",".");
          fullHourLabels.push({x:xAt(timestamp),label});
        }
      }
      const maxLabels=Math.max(3,Math.floor(plotW/54)+1);
      const stride=Math.max(1,Math.ceil(fullHourLabels.length/maxLabels));
      timeLabels=fullHourLabels.filter((_,index)=>index%stride===0);
    }else if(period==="year"){
      const monthFormatter=new Intl.DateTimeFormat("pl-PL",{timeZone:timezone,month:"short",year:"2-digit"});
      const monthTicks=[firstTimestamp,...monthBoundaries.filter((timestamp)=>timestamp>firstTimestamp+60000)];
      const monthStride=Math.max(1,Math.ceil(monthTicks.length*40/plotW));
      timeLabels=monthTicks.filter((_,index)=>index===0||index%monthStride===0).map((timestamp)=>({
        x:xAt(timestamp),
        label:monthFormatter.format(new Date(timestamp)).replace(".","")
      }));
    }else{
      const labelCount=Math.min(8,Math.max(3,Math.floor(plotW/120)+1));
      const labelStyle=period==="week"?{weekday:"short",hour:"2-digit"}:{day:"2-digit",month:"2-digit"};
      timeLabels=Array.from({length:labelCount},(_,index)=>{
        const timestamp=firstTimestamp+(lastTimestamp-firstTimestamp)*index/(labelCount-1);
        return {x:xAt(timestamp),label:dateTime(timestamp,labelStyle)};
      });
    }
    timeLabels.forEach((item,index)=>{
      const anchor=index===0?"start":index===timeLabels.length-1?"end":"middle";
      element("text",{x:item.x,y:height-8,"text-anchor":anchor,class:"axis-label"},item.label);
    });
    usable.forEach((item,index)=>{
      const dot=element("circle",{cx:x(index),cy:y(item.average),r:3.4,class:"dot",stroke:metric==="humidity"?"#5b82a8":"#26785f"});
      dot.appendChild(document.createElementNS(ns,"title")).textContent=dateTime(item.at,{day:"numeric",month:"long",hour:"2-digit",minute:"2-digit"})+": "+number(item.average)+" "+unit+" (min "+number(item.min)+", max "+number(item.max)+", n="+item.samples+")";
    });
    container.replaceChildren(svg);
  }

  function render() {
    const current=currentData || {};
    const history=historyData || {};
    timezone=(current.site && current.site.timezone)||(history.site && history.site.timezone)||timezone;
    $("siteLabel").textContent=(current.site && current.site.name)||(history.site && history.site.name)||"Stacja pogodowa";
    $("nodeLabel").textContent=(current.node && current.node.name)||(history.node && history.node.name)||$("siteLabel").textContent;
    $("rangeLabel").textContent=periodLabels[period]+" · agregaty temperatury i wilgotności";
    latestWeather(current);
    const devices=history.devices||[];
    const weather=devices.find((item)=>item.type==="weather_sensor")||devices[0];
    const currentWeather=(current.devices||[]).find((item)=>item.type==="weather_sensor");
    const points=weather?weather.points||[]:[];
    updateDataStatus(currentWeather,weather,history);
    chart($("temperatureChart"),points,"temperature","°C",history.bucket_seconds);
    chart($("humidityChart"),points,"humidity","%",history.bucket_seconds);
    $("updatedAt").textContent=dateTime(new Date().toISOString(),{hour:"2-digit",minute:"2-digit",second:"2-digit"});
  }

  async function load() {
    const notice=$("notice");
    notice.style.display="none";
    try {
      const [currentResponse,historyResponse]=await Promise.all([
        fetch("/api/v1/public/current",{cache:"no-store"}),
        fetch("/api/v1/public/history?period="+encodeURIComponent(period),{cache:"no-store"})
      ]);
      if(!currentResponse.ok||!historyResponse.ok) throw new Error("Serwer zwrócił błąd podczas pobierania danych.");
      [currentData,historyData]=await Promise.all([currentResponse.json(),historyResponse.json()]);
      render();
    } catch(error) {
      notice.textContent="Nie udało się pobrać danych: "+error.message;
      notice.style.display="block";
    }
  }

  window.addEventListener("resize",()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(render,120);});
  load();
  window.setInterval(load,60000);
})();
</script>
</body>
</html>
"""
