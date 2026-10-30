import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TranslatePipe } from '../i18n';
import { CommentsList } from '../lists/comments-list';
import { Post, User } from '../models';
import { Status, WriteStatus } from '../status';
import { ResourceItem } from '../store';
import { ConfirmButton } from '../ui/confirm-button';
import { EntityForm } from '../ui/entity-form';

@Component({
  selector: 'app-post-detail-page',
  imports: [
    RouterLink,
    TranslatePipe,
    Status,
    WriteStatus,
    ConfirmButton,
    EntityForm,
    CommentsList,
  ],
  templateUrl: './post-detail-page.html',
})
export class PostDetailPage {
  /** Paramètre :id de l'URL. */
  readonly id = input.required<string>();

  protected readonly post = new ResourceItem<Post>('posts', () => this.id());
  protected readonly author = new ResourceItem<User>('users', () => this.post.value()?.user_id);
}
