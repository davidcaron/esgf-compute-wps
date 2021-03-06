import { Component } from '@angular/core';

@Component({
  template: `
  <div class="container">
    <h1 class="text-center">Welcome to LLNL's CWT WPS server</h1>
    <div class="row">
      <div class="col-md-12">
        <br>
        <p>
          To get started, login using <a routerLink="/wps/home/auth/login/openid">OpenID</a>.
        </p>
        <p>
          To access ESGF data you will need to retrieve a certificate through OAuth2 or MyProxyClient.
          These options are found on the bottom of the user <a routerLink="/wps/home/user/profile">Profile</a> page.
        </p>
        <p>
          After requesting a certificate, you will find your API key on the user <a routerLink="/wps/home/user/profile">Profile</a>.
          You can use this to access the ESGF WPS services through then ESGF CWT End-user API which can be install from <a target="_blank" href="https://anaconda.org/uvcdat/esgf-compute-api">Conda</a>. Examples of the API can be found <a target="_blank" href="https://github.com/ESGF/esgf-compute-api/tree/master/examples">here</a>.
        </p>
      </div>
    </div>
  </div>
  `
})
export class HomeComponent {}
