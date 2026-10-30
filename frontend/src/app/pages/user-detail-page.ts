import { Component, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TranslatePipe } from '../i18n';
import { TitledList } from '../lists/titled-list';
import { TodosList } from '../lists/todos-list';
import { User } from '../models';
import { Status, WriteStatus } from '../status';
import { ResourceItem } from '../store';
import { ConfirmButton } from '../ui/confirm-button';
import { EntityForm } from '../ui/entity-form';

@Component({
  selector: 'app-user-detail-page',
  imports: [
    RouterLink,
    TranslatePipe,
    Status,
    WriteStatus,
    ConfirmButton,
    EntityForm,
    TitledList,
    TodosList,
  ],
  templateUrl: './user-detail-page.html',
})
export class UserDetailPage {
  /** Paramètre :id de l'URL. */
  readonly id = input.required<string>();

  protected readonly user = new ResourceItem<User>('users', () => this.id());
  protected readonly tabs = ['posts', 'albums', 'todos'] as const;
  protected readonly tab = signal<(typeof this.tabs)[number]>('posts');
}
