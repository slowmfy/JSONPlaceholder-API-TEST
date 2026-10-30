import { provideHttpClient, withFetch } from '@angular/common/http';
import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';

import { routes } from './app.routes';
import { I18n } from './i18n';
import { Schema } from './schema';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideHttpClient(withFetch()),
    // withComponentInputBinding : le paramètre :id de l'URL arrive dans l'input `id` du composant.
    provideRouter(routes, withComponentInputBinding()),
    // Les traductions et la description des ressources sont chargées avant le premier affichage.
    provideAppInitializer(() => {
      const i18n = inject(I18n);
      const schema = inject(Schema);
      return Promise.all([i18n.init(), schema.init()]);
    }),
  ],
};
