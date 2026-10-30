import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { I18n, TranslatePipe } from './i18n';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, TranslatePipe],
  templateUrl: './app.html',
})
export class App {
  protected readonly i18n = inject(I18n);

  protected async changeLanguage(event: Event): Promise<void> {
    const select = event.target as HTMLSelectElement;
    try {
      await this.i18n.use(select.value);
    } catch {
      select.value = this.i18n.language(); // serveur injoignable : la langue ne change pas
    }
  }
}
