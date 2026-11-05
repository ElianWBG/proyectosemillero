"use strict";
(() => {
 const key='visorlab-theme';
 const picker=document.getElementById('theme');
 function apply(value){
  const theme=['original','midnight','clean'].includes(value)?value:'clean';
  document.body.dataset.theme=theme;
  picker.value=theme;
  try{localStorage.setItem(key,theme);}catch{/* La app también funciona sin almacenamiento local. */}
  window.dispatchEvent(new Event('themechange'));
 }
 let saved='clean';
 try{saved=localStorage.getItem(key)||saved;}catch{}
 apply(saved);
 picker.addEventListener('change',()=>apply(picker.value));
})();
