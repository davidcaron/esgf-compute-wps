import { Component } from '@angular/core';
import { Router } from '@angular/router';

import { User } from '../user/user.service';
import { AuthService } from '../core/auth.service';
import { NotificationService } from '../core/notification.service';

@Component({
  templateUrl: './create-user.component.html',
  styleUrls: ['../forms.css']
})

export class CreateUserComponent {
  model: User = new User();

  constructor(
    private authService: AuthService,
    private notificationService: NotificationService,
    private router: Router
  ) { }

  onSubmit(): void {
    this.authService.create(this.model)
      .then(response => {
        this.router.navigate(['/wps/home/auth/login']);
      })
      .catch(error => {
        this.notificationService.error(`Failed creating account: "${error}"`);
      });
  }
}
