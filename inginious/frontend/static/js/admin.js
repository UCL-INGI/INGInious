//
// This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
// more information about the licensing of this file.
//
function revoke_binding(event){
    var username = $(this).data("username");
    var binding_id = $(this).data("binding");
    $.post({
      url: "user_action",
      data: {
        "username":username,
        "action":"revoke_binding",
        "binding_id": binding_id
      },
    }).done(function(feedback) {
        if (!feedback.hasOwnProperty('error')){
            window.location.href = "users";
        }else{
            $('#feedback_bindings').text(feedback['message']);
            $('#feedback_bindings').show();
        }
    });
}
function get_bindings(username){
    var bindings = {};
    $.post({
      async: false,
      url: "user_action",
      data: {
        "username":username,
        "action":"get_bindings",
      },
    }).done(function(result) {
        bindings = result;
    });
    return bindings;
}
function display_bindings(username,bindings){
    for (var elem in bindings) {
        var template = $('#hidden-template').clone();
        template = $(template).children("div.card.mb-3").first().attr('id',elem+'-template').parent().html();
        $("#binding_content").append(template);
        $("#"+elem+"-template .binding_revoke").data("username",username);
        $("#"+elem+"-template .binding_revoke").data("binding",elem);
        $("#"+elem+"-template .binding_identifier").text(bindings[elem][0]);
        $("#"+elem+"-template .binding_method").text(elem);
    }
    $('.binding_revoke').bind("click", revoke_binding);
}

function action_handler(action){
    var username=$('#username').val();
    var realname = "";
    var email = "";
    var password = "";
    if (action == "add_user"){
        username = $('input[name="usrname"]').val();
        realname = $('input[name="realname"]').val();
        email = $('input[name="email"]').val();
        password = $('input[name="password"]').val();
    }
    $.post({
      url: "user_action",
      data: {
        "username":username,
        "realname":realname,
        "email": email,
        "password":password,
        "action":action
      },
    }).done(function(feedback) {
        if (!feedback.hasOwnProperty('error')){
            window.location.href = "users";
        }else{
            $('#feedback').text(feedback['message']);
            $('#feedback').show();
        }
    });
}