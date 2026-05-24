import { Context } from 'telegraf';

export interface MySession {
  language: string;
  role?: 'BUYER' | 'CHEF' | 'ADMIN';
  h3Index?: string;
  activeOrderId?: string;
}

export interface MyContext extends Context {
  session: MySession;
}
