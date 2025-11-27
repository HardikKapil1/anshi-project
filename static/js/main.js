function doSearch(form){
  // simple client-side guard: trim
  const q = (form.q.value||'').trim();
  form.q.value = q;
  return true; // allow submission
}

function contactOwner(itemId){
  const msg = prompt('Write a short message to the owner (include contact info)');
  if(!msg) return;
  // send via fetch to /contact API (needs backend route)
  fetch('/contact', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({item_id: itemId, message: msg})
  }).then(r=>r.json()).then(resp=>{
    if(resp.success) alert('Message sent to owner');
    else alert('Could not send message');
  }).catch(e=>alert('Network error'));
}
