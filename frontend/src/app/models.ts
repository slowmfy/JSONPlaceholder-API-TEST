// Formes des objets renvoyés par l'API web (web_api.py), elles-mêmes issues de models.py.

export interface Item {
  id: number;
}

export interface User extends Item {
  name: string;
  username: string;
  email: string;
  phone: string;
  website: string;
  street: string;
  suite: string;
  zipcode: string;
  city: string;
  company_name: string;
  company_catchphrase: string;
}

export interface Post extends Item {
  user_id: number;
  title: string;
  body: string;
}

export interface Comment extends Item {
  post_id: number;
  name: string;
  email: string;
  body: string;
}

export interface Album extends Item {
  user_id: number;
  title: string;
}

export interface Photo extends Item {
  album_id: number;
  title: string;
  url: string;
  thumbnail_url: string;
}

export interface Todo extends Item {
  user_id: number;
  title: string;
  completed: boolean;
}

export interface UserReport {
  user: User;
  post_count: number;
  comment_count: number;
  most_commented: { post: Post; comments: number; ties: number } | null;
  posts: { post: Post; comments: number }[];
}

export interface WriteResult<T> {
  item: T;
  simulated: boolean;
}

export interface Language {
  code: string;
  name: string;
}

/** Erreur renvoyée par l'API : une clé de traduction, ses paramètres et le champ en faute. */
export interface ApiError {
  key: string;
  params: Record<string, unknown>;
  field?: string | null;
}

/** Message de réussite après une écriture. */
export interface Feedback {
  key: string;
  params: Record<string, unknown>;
  /** Vrai pour une écriture : JSONPlaceholder ne l'a pas réellement enregistrée. */
  simulated: boolean;
}

/** Description d'un champ, fournie par /api/schema (resources.py). */
export interface FieldDef {
  name: string;
  kind: 'text' | 'textarea' | 'email' | 'url' | 'phone' | 'bool' | 'ref';
  required: boolean;
  ref: string | null;
}

export interface ResourceSchema {
  name: string;
  fields: FieldDef[];
  filters: string[];
}

export interface RefOption {
  id: number;
  label: string;
}

export interface ExplorerResult {
  status: number;
  elapsed_ms: number;
  body: unknown;
}
