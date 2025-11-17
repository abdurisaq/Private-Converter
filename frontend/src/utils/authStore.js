import { create } from 'zustand';

export const useAuthStore = create((set, get) => ({
  access: typeof window !== 'undefined' ? localStorage.getItem('access') : null,
  refresh: typeof window !== 'undefined' ? localStorage.getItem('refresh') : null,
  user: (() => {
    if (typeof window === 'undefined') return null;
    try {
      return JSON.parse(localStorage.getItem('user')) || null;
    } catch {
      localStorage.removeItem('user');
      return null;
    }
  })(),

  setAuth: (access, refresh, user) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access', access);
      localStorage.setItem('refresh', refresh);
      localStorage.setItem('user', JSON.stringify(user));
    }
    set({ access, refresh, user });
  },

  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      localStorage.removeItem('user');
    }
    set({ access: null, refresh: null, user: null });
  },

  isAuthenticated: () => Boolean(get().access),

  isAdmin: () => get().user?.role === 'admin',
}));


export default useAuthStore;
