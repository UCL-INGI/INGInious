//var x=document.getElementsByClassName("itemHeader")[0];
//console.log(x);
//x.className+=" div-title-content";

jQuery(document).ready(function($) {
  var backgroundImages=["fondo2.jpg","fondo3.jpg","fondo1.jpg","fondo4.jpg","fondo5.jpg","fondo6.jpg"];
  index=Math.floor((Math.random() * backgroundImages.length));
  $(".detalle").addClass("detalle-background");
  $(".detalle-background").css("background-image", "url( //ingenieria.bogota.unal.edu.co/images/recursos/sliderProgramasAcademicos/fondosContenido/"+String(backgroundImages[index])+")");
  
});

window.onresize = function(){ location.reload(); }

