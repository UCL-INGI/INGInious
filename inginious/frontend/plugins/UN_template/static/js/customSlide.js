imagesSlide=["banner-edi.jpg","banner-estudiantes.jpg","banner-egresados.jpg","banner-todos.jpg","banner-candidatos2.jpg","banner-candidatos1.jpg","banner-catedra.jpg","banner-metrologia.jpg","portada1.jpg"];
hrefimagesSlide=["#","https://ingenieria.bogota.unal.edu.co/designacion-decano/index.php/calendario/calendario-facultad","https://ingenieria.bogota.unal.edu.co/designacion-decano/index.php/calendario/calendario-facultad","https://ingenieria.bogota.unal.edu.co/designacion-decano/index.php/calendario/calendario-facultad","https://ingenieria.bogota.unal.edu.co/designacion-decano","#","https://ingenieria.bogota.unal.edu.co/catedra-internacional-2018","https://ingenieria.bogota.unal.edu.co/uec/?p=5303","#"];
var indexSlide=0;



function preload(arrayOfImages) {
    jQuery(arrayOfImages).each(function(){
        jQuery('<img/>')[0].src = "/images/slider2/" + this;
    });
}

preload(imagesSlide)


  function changeImageSlide(){
    if (indexSlide==imagesSlide.length) {
      indexSlide=0;
    }
    else if (indexSlide<0) {
      indexSlide=imagesSlide.length-1;
    }
    var image="/images/slider2/"+imagesSlide[indexSlide];
    var url=hrefimagesSlide[indexSlide];
    var e=jQuery("#img-myslide").parent();
    jQuery("#img-myslide").fadeOut(1000, function() {
      e.attr("href", url);
      if(url!="#"){
        e.removeClass("a_disabled");
      }
      else{
        e.addClass("a_disabled");
      }
      jQuery("#img-myslide").attr('src',image);
    }).fadeIn(1000);
  }
  
  
  
  var auto = setInterval(function (){
    indexSlide+=1;
    changeImageSlide();
  }, 7000)
  
  
  function resetInterval(){
    clearInterval(auto);
    auto = setInterval(function (){
      indexSlide+=1;
      changeImageSlide();
    }, 7000);
  }
  
  function next(){
    indexSlide+=1;
    changeImageSlide();
    resetInterval();
  }
  
  function previus(){
    indexSlide-=1;
    changeImageSlide();
    resetInterval();
  }
  







