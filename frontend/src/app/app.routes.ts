import { Routes } from '@angular/router';

import { TitledList } from './lists/titled-list';
import { TodosList } from './lists/todos-list';
import { AlbumDetailPage } from './pages/album-detail-page';
import { ExplorerPage } from './pages/explorer-page';
import { PostDetailPage } from './pages/post-detail-page';
import { UserDetailPage } from './pages/user-detail-page';
import { UserReportPage } from './pages/user-report-page';
import { UsersPage } from './pages/users-page';

export const routes: Routes = [
  { path: '', redirectTo: 'users', pathMatch: 'full' },
  { path: 'users', component: UsersPage },
  { path: 'users/:id', component: UserDetailPage },
  { path: 'users/:id/report', component: UserReportPage },
  { path: 'posts', component: TitledList, data: { resource: 'posts' } },
  { path: 'posts/:id', component: PostDetailPage },
  { path: 'albums', component: TitledList, data: { resource: 'albums' } },
  { path: 'albums/:id', component: AlbumDetailPage },
  { path: 'todos', component: TodosList },
  { path: 'explorer', component: ExplorerPage },
  { path: '**', redirectTo: 'users' },
];
