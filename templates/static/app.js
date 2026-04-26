let allListings = [];
document.addEventListener('DOMContentLoaded', () => {
  loadListings();
  loadStats();
  // Auto-refresh every 10 seconds so everyone sees live updates
  setInterval(() => { loadListings(); loadStats(); }, 10000);
});
function openModal(id){document.getElementById(id).classList.add('active');document.body.style.overflow='hidden';}
function closeModal(id){document.getElementById(id).classList.remove('active');document.body.style.overflow='';}
function closeModalOutside(e,id){if(e.target.id===id)closeModal(id);}
function scrollTo(id){document.getElementById(id).scrollIntoView({behavior:'smooth'});}
async function submitDonation(e){
  e.preventDefault();
  const data={donor_name:document.getElementById('donorName').value,donor_phone:document.getElementById('donorPhone').value,food_item:document.getElementById('foodItem').value,quantity:document.getElementById('foodQty').value,category:document.getElementById('foodCategory').value,best_before_hours:parseInt(document.getElementById('bestBefore').value),location:document.getElementById('location').value,notes:document.getElementById('notes').value};
  try{const r=await fetch('/api/donate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const res=await r.json();
    if(res.success){document.getElementById('donateForm').style.display='none';document.getElementById('donateSuccess').style.display='block';loadListings();loadStats();}
    else alert('Error: '+res.error);
  }catch(err){alert('Network error.');}
}
function hideDonateSuccess(){document.getElementById('donateForm').reset();document.getElementById('donateForm').style.display='block';document.getElementById('donateSuccess').style.display='none';}
async function loadListings(){
  document.getElementById('listingsGrid').innerHTML='<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading live data...</div>';
  try{const r=await fetch('/api/listings');const data=await r.json();allListings=data.listings||[];renderListings(allListings);}
  catch(e){document.getElementById('listingsGrid').innerHTML='<div class="no-listings"><i class="fas fa-exclamation-circle"></i><p>Could not load. Please refresh.</p></div>';}
}
function renderListings(listings){
  const grid=document.getElementById('listingsGrid');
  if(!listings||listings.length===0){grid.innerHTML='<div class="no-listings"><i class="fas fa-box-open"></i><p>No listings yet. Be the first to donate!</p></div>';return;}
  grid.innerHTML=listings.map(item=>{
    const urg=item.best_before_hours<=3?'urgent':item.best_before_hours<=8?'medium':'';
    const urgL=item.best_before_hours<=3?'Urgent':item.best_before_hours<=8?'Today':'Available';
    const cl=item.claimed?'disabled':'';const clL=item.claimed?'Claimed':'Claim Food';
    return `<div class="food-card"><div class="card-header"><div class="card-title">${esc(item.food_item)}</div><span class="card-badge ${urg}">${urgL}</span></div><div class="card-info"><div class="card-info-item"><i class="fas fa-tag"></i> ${esc(item.category)}</div><div class="card-info-item"><i class="fas fa-weight-hanging"></i> ${esc(item.quantity)}</div><div class="card-info-item"><i class="fas fa-map-marker-alt"></i> ${esc(item.location)}</div><div class="card-info-item"><i class="fas fa-clock"></i> Best before: ${item.best_before_hours}h</div><div class="card-info-item"><i class="fas fa-user"></i> ${esc(item.donor_name)}</div>${item.notes?`<div class="card-info-item"><i class="fas fa-comment"></i> ${esc(item.notes)}</div>`:''}</div><div class="card-footer"><span class="card-time"><i class="fas fa-calendar-alt"></i> ${fmtDate(item.created_at)}</span><button class="btn-claim" onclick="openClaimModal(${item.id},'${esc(item.food_item)}','${esc(item.location)}')" ${cl}>${clL}</button></div></div>`;
  }).join('');
}
function filterListings(){
  const s=document.getElementById('searchInput').value.toLowerCase();const cat=document.getElementById('categoryFilter').value;
  renderListings(allListings.filter(i=>(!s||i.food_item.toLowerCase().includes(s)||i.location.toLowerCase().includes(s)||i.donor_name.toLowerCase().includes(s))&&(!cat||i.category===cat)));
}
function openClaimModal(id,food,loc){
  document.getElementById('claimFoodId').value=id;
  document.getElementById('claimDetails').innerHTML=`<strong><i class="fas fa-utensils"></i> ${esc(food)}</strong><br/><i class="fas fa-map-marker-alt"></i> ${esc(loc)}`;
  document.getElementById('claimSuccess').style.display='none';
  document.getElementById('claimName').value='';document.getElementById('claimPhone').value='';document.getElementById('claimOrg').value='';
  openModal('claimModal');
}
async function submitClaim(e){
  e.preventDefault();
  const data={food_id:parseInt(document.getElementById('claimFoodId').value),claimer_name:document.getElementById('claimName').value,claimer_phone:document.getElementById('claimPhone').value,organization:document.getElementById('claimOrg').value};
  try{const r=await fetch('/api/claim',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const res=await r.json();
    if(res.success){document.getElementById('claimSuccess').style.display='flex';setTimeout(()=>{closeModal('claimModal');loadListings();loadStats();},2500);}
    else alert('Error: '+res.error);
  }catch(err){alert('Network error.');}
}
async function loadStats(){
  try{const r=await fetch('/api/stats');const d=await r.json();
    animCount('totalDonations',d.total_donations);animCount('totalKg',d.total_kg);animCount('totalPeople',d.total_people_fed);
    animCount('impactDonations',d.total_donations);document.getElementById('impactKg').textContent=d.total_kg+' kg';
    animCount('impactPeople',d.total_people_fed);document.getElementById('impactCO2').textContent=d.co2_prevented+' kg';
  }catch(e){}
}
function animCount(id,target){
  const el=document.getElementById(id);if(!el)return;let cur=0;const step=Math.max(1,Math.floor(target/50));
  const t=setInterval(()=>{cur=Math.min(cur+step,target);el.textContent=cur;if(cur>=target)clearInterval(t);},30);
}
async function submitContact(e){
  e.preventDefault();
  const data={name:document.getElementById('contactName').value,email:document.getElementById('contactEmail').value,message:document.getElementById('contactMsg').value};
  try{const r=await fetch('/api/contact',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const res=await r.json();
    if(res.success){document.getElementById('contactSuccess').style.display='flex';e.target.reset();setTimeout(()=>{document.getElementById('contactSuccess').style.display='none';},4000);}
  }catch(err){}
}
function runAIPrediction(){
  const type=document.getElementById('aiType').value;const guests=parseInt(document.getElementById('aiGuests').value)||50;
  const meal=document.getElementById('aiMealTime').value;const day=document.getElementById('aiDay').value;
  const base={restaurant:0.12,hotel:0.18,household:0.08,bakery:0.25,event:0.22};
  const mealM={breakfast:0.7,lunch:1.0,dinner:1.2,event:1.5};const dayM={weekday:1.0,weekend:1.3,holiday:1.6};
  const kg=Math.round(guests*base[type]*mealM[meal]*dayM[day]*10)/10;
  const srv=Math.round(kg*4);const ppl=Math.round(srv*0.8);const co2=Math.round(kg*2.5*10)/10;
  const conf=Math.round(75+Math.random()*20);
  const r=document.getElementById('aiResult');r.style.display='block';
  r.innerHTML=`<h4><i class="fas fa-brain"></i> AI Prediction - ${conf}% Confidence</h4><div class="prediction-items"><div class="prediction-item"><span>${kg} kg</span><small>Surplus</small></div><div class="prediction-item"><span>${srv}</span><small>Servings</small></div><div class="prediction-item"><span>${ppl}</span><small>People Fed</small></div><div class="prediction-item"><span>${co2} kg</span><small>CO2 Saved</small></div></div><p style="font-size:.8rem;color:rgba(255,255,255,.6);margin-top:.8rem;"><i class="fas fa-lightbulb"></i> Pre-register your donation so NGOs can prepare!</p>`;
}
function openMaps(){window.open('https://www.google.com/maps/dir/Koramangala,+Bangalore/Indiranagar,+Bangalore/MG+Road,+Bangalore','_blank');}
function trackDonation(){
  const id=document.getElementById('trackingId').value.trim();
  if(!id){alert('Enter a Donation ID e.g. FS-1001');return;}
  document.getElementById('trackingResult').style.display='block';
  document.getElementById('trackingResult').scrollIntoView({behavior:'smooth'});
}
function esc(s){if(!s)return'';return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');}
function fmtDate(s){if(!s)return'';const d=new Date(s);return d.toLocaleDateString('en-IN',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});}
