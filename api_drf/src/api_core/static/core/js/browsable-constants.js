if (!window._ACCESS_TOKEN_STORAGE_KEY_) {
    window._ACCESS_TOKEN_STORAGE_KEY_ = '_access_token_';
}

if (!window._AUTH_ACTIONS_) {
    window._AUTH_ACTIONS_ = [
        '/api/v1/auth/signin',
        '/api/v1/auth/signin/second_factor',
        '/api/v1/auth/signup/second_factor',
        '/api/v1/auth/signup'
    ]
}
