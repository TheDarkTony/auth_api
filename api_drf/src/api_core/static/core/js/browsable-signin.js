
function storeAuthTokenFromAuthPages(){
  post_form = $('#post-object-form')
  if (post_form === undefined){ return; }
  
  resp_form = post_form.find('form')
  if (resp_form == undefined){ return; }
  
  action = resp_form.attr('action');
  if (action == undefined){ return; }

  if (window._AUTH_ACTIONS_.includes(action))
  {
    access_token_output = resp_form.find("input[name='body.access_token']")
    if (access_token_output === undefined){ return; }

    token = access_token_output.val()
    if (token === undefined || token === ''){ return; }

    localStorage.setItem(window._ACCESS_TOKEN_STORAGE_KEY_, token);
    document.cookie = window._ACCESS_TOKEN_STORAGE_KEY_+'='+token+ '; path=/;'
  }
}

$(document).ready(function() {
  storeAuthTokenFromAuthPages()
});
