/*Buscador*/
"use strict";
(function() {
  var cx = '008572255874373046644:chip1p1uf-4';
  var gcse = document.createElement('script');
  gcse.type = 'text/javascript';
  gcse.async = true;
  gcse.src = (document.location.protocol == 'https:' ? 'https:' : 'http:') +
  '//www.google.com/cse/cse.js?cx=' + cx;
  var s = document.getElementsByTagName('script')[0];
  s.parentNode.insertBefore(gcse, s);
})();

function checkBck() {
  if (jQuery('.gsc-search-button input').attr('src')) {
    jQuery('.gsc-search-button input').attr('src', 'http://unal.edu.co/fileadmin/templates/images/search.png');
    jQuery('.gsc-input input').attr('placeholder', 'Buscar en la Universidad');
  } else {
    window.setTimeout(function() { checkBck(); }, 100);
  }
}
checkBck();

jQuery(document).ready(function($) {
    
  
  $('#unalOpenMenuServicios, #unalOpenMenuPerfiles').on('click',function(e) {
    var $target = $(this).data('target');
    var $mOffset = $(this).offset();
    $($target)
    .css({ top: $mOffset.top + $(this).outerHeight(), left: $mOffset.left })
  });

  function serviceMenuStatus() {
    var $s = $('#services');
    $s.height($(window).height());
    $('ul', $s).height($(window).height());
    
    if ($('.indicator', '#services').hasClass('active')) {
      $s.css({ 'right': 0 });
    } else {
      $s.css({ 'right': parseInt($('#services').width()) * -1 });
    }
  }
  
  $('.indicator', '#services').click(function() {
    $(this).toggleClass('active');
    serviceMenuStatus();
  });
  
  $(window).resize(function() {
    $('.open').removeClass('open');
    if ($(window).width() > 767) {
      $('#services').css({ 'right': parseInt($('#services').width()) * -1, left: 'auto', top: 'auto' });
      $('#bs-navbar').removeClass('in')
      serviceMenuStatus();
    } else {
      $('.indicator', '#services').removeClass('active');
    }  
  });
  $('#services').css({ 'right': parseInt($('#services').width()) * -1 })
  serviceMenuStatus();

  /*Menu lateral programas academicos y Ancla*/

    function crearFilaAsignatura(value, id, ar){
      if(value.tipologia=='T'){
        value.tipologia='E'
      }
      if(value.tipologia=='O'){
        value.tipologia='O'
      }
      $("#asignaturasSIA").append('<div class="siaAsignatura" id="siaAsignatura_'+id+'" style="display: none">');
      $("#siaAsignatura_"+id).append('<div class="siaTipologia">'+ value.tipologia +'</div>');
      $("#siaAsignatura_"+id).append('<div class="siaDetalle"><div class="siaNombre">'+ value.nombre +'</div>'
       + '<div class="siaCodigo"> Código SIA '+ value.codigo +'</div>'
       + '<div class="siaCreditos">Créditos '+ value.creditos +'</div></div>');
      $("#asignaturasSIA").append('</div>');
      $("#siaAsignatura_"+id).fadeIn('slow');
    }

    var asignaturas;
    function cargarAsignaturasSIA(asignatura){
      $.ajax({
        url: '/sia/remoteservices',
        type: 'POST',
        contentType: 'application/json',
        dataType: 'json',
        data: JSON.stringify({
          jsonrpc: '2.0',
          method: 'buscador.obtenerAsignaturas',
          params: ["", "PRE", "", "POS", asignatura, "", 1, "180"]
        }),
      }).done(function(data) {
        asignaturas = data.result.asignaturas.list;
        asignaturas.sort()
        $('#asignaturasSIA').empty()
        asignaturas.forEach(crearFilaAsignatura)
      });
    }

    if($('#asignaturasSIA').length>0) {
      cargarAsignaturasSIA($('#asignaturasSIA')[0].getAttribute("coodigoSIA"))
    }

    /**
     *  Inicio modificacion UNCode
     */

    $('#wrapper').find('> div.navbar.navbar-default.navbar-static-top > div > div.navbar-header > a > img').attr("src", window.location.origin + "/UN_template/static/images/LogotipoUNAL.png")
    var footer = $('#footer');
    footer.find('> div > div > div > p').html(' &copy; 2017-' + (new Date()).getFullYear() + ' Universidad Nacional de Colombia')
    footer.find('> div > div > div > div > p').html('<a target="_blank" href="https://github.com/JuezUN/INGInious" class="navbar-link">\n' +
                                                    'UNCode is distributed under AGPL license' +
                                                    '</a>' + ' - <a target="_blank" href="http://www.inginious.org" class="navbar-link">\n' +
                                                    'Powered by INGInious\n</a>');

    //favicon
     $('link[rel="icon"]').attr('href',  window.location.origin + "/UN_template/static/images/LogotipoUNAL.png");

    /**
     *  fin modificacion UNCode
     */


});







