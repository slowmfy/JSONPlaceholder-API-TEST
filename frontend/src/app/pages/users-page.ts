import { Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { TranslatePipe } from '../i18n';
import { User } from '../models';
import { Status, WriteStatus } from '../status';
import { ResourceList } from '../store';
import { ConfirmButton } from '../ui/confirm-button';
import { EntityForm } from '../ui/entity-form';

@Component({
  selector: 'app-users-page',
  imports: [RouterLink, TranslatePipe, Status, WriteStatus, ConfirmButton, EntityForm],
  templateUrl: './users-page.html',
})
export class UsersPage {
  private readonly router = inject(Router);
  protected readonly list = new ResourceList<User>('users');

  protected readonly search = signal('');
  protected readonly filtered = computed(() => {
    const term = this.search().trim().toLowerCase();
    return this.list
      .items()
      .filter((user) =>
        [user.name, user.email, user.city ?? ''].some((value) =>
          value.toLowerCase().includes(term),
        ),
      );
  });

  // Accès direct : l'identifiant est validé côté serveur (validators.py),
  // la page de destination affiche le message d'erreur éventuel.
  protected readonly targets = [
    { label: 'goto_user', route: 'users', value: signal('') },
    { label: 'goto_post', route: 'posts', value: signal('') },
    { label: 'goto_album', route: 'albums', value: signal('') },
  ];

  protected open(route: string, raw: string): void {
    const id = raw.trim();
    if (id) {
      this.router.navigate([`/${route}`, id]);
    }
  }
}
