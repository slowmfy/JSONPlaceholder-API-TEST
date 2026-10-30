import { Component, computed, inject, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Api, valueOf } from '../api';
import { TranslatePipe } from '../i18n';
import { Status } from '../status';

@Component({
  selector: 'app-user-report-page',
  imports: [RouterLink, TranslatePipe, Status],
  templateUrl: './user-report-page.html',
})
export class UserReportPage {
  /** Paramètre :id de l'URL. */
  readonly id = input.required<string>();

  protected readonly report = inject(Api).userReport(() => this.id());
  protected readonly reportData = valueOf(this.report);

  /** Plus grand nombre de commentaires, pour dimensionner les barres. */
  protected readonly maxComments = computed(() =>
    Math.max(1, ...(this.reportData()?.posts ?? []).map((entry) => entry.comments)),
  );
}
