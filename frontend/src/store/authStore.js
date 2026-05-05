import { create } from 'zustand';
import { me } from '../services/authService';
import { getAccess, clearTokens } from '../utils/tokenStorage';

const useAuthStore = create((set) => ({
  user: null,
  loading: true,

  init: async () => {
    if (!getAccess()) { set({ loading: false }); return; }
    try {
      const user = await me();
      set({ user, loading: false });
    } catch {
      clearTokens();
      set({ user: null, loading: false });
    }
  },

  setUser: (user) => set({ user }),

  logout: () => {
    clearTokens();
    set({ user: null });
  },
}));

export default useAuthStore;
