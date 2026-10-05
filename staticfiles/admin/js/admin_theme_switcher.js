/**
 * Theme Switcher para Django Admin - VentaControl Pro
 * ====================================================
 * Soporta cambio fluido entre Modo Blanco (Sol ☀️) y Modo Negro (Luna 🌙).
 * Persiste la elección en localStorage y actualiza clases y atributos en tiempo real.
 */

(function () {
    'use strict';

    const STORAGE_KEY = 'admin_theme';

    function getPreferredTheme() {
        const stored = localStorage.getItem(STORAGE_KEY) || localStorage.getItem('theme');
        if (stored === 'light' || stored === 'dark') {
            return stored;
        }
        // Por defecto usar 'light' (blanco) para una bienvenida limpia y luminosa
        return 'light';
    }

    function applyTheme(theme) {
        const root = document.documentElement;
        const isDark = theme === 'dark';

        // Actualizar atributos de datos y clases para máxima compatibilidad con Django 5/6 y CSS personalizado
        root.dataset.theme = theme;
        root.setAttribute('data-theme', theme);
        root.setAttribute('data-admin-theme', theme);

        if (document.body) {
            document.body.classList.remove('theme-light', 'theme-dark');
            document.body.classList.add(isDark ? 'theme-dark' : 'theme-light');
        }

        localStorage.setItem(STORAGE_KEY, theme);
        localStorage.setItem('theme', theme);

        // Actualizar el estado visual de todos los botones de cambio de tema
        updateToggleButtons(theme);
    }

    function updateToggleButtons(theme) {
        const buttons = document.querySelectorAll('.theme-toggle-btn, .admin-theme-switch');
        const isDark = theme === 'dark';

        buttons.forEach(btn => {
            btn.setAttribute('data-current-theme', theme);
            btn.setAttribute('aria-label', isDark ? 'Modo Negro activo (Luna). Clic para cambiar a Blanco (Sol)' : 'Modo Blanco activo (Sol). Clic para cambiar a Negro (Luna)');
            btn.setAttribute('title', isDark ? 'Cambiar a Modo Blanco (Sol ☀️)' : 'Cambiar a Modo Negro (Luna 🌙)');

            // Actualizar contenido interior si contiene los contenedores de Sol y Luna
            const sunIcon = btn.querySelector('.theme-icon-sun');
            const moonIcon = btn.querySelector('.theme-icon-moon');
            const labelText = btn.querySelector('.theme-label-text');

            if (sunIcon && moonIcon) {
                if (isDark) {
                    // Modo Negro activo: El botón muestra la LUNA 🌙
                    sunIcon.style.display = 'none';
                    moonIcon.style.display = 'inline-flex';
                } else {
                    // Modo Blanco activo: El botón muestra el SOL ☀️
                    sunIcon.style.display = 'inline-flex';
                    moonIcon.style.display = 'none';
                }
            }

            if (labelText) {
                labelText.textContent = isDark ? 'Modo Negro' : 'Modo Blanco';
            }
        });
    }

    function toggleTheme() {
        const current = getPreferredTheme();
        const nextTheme = current === 'dark' ? 'light' : 'dark';
        
        // Animación suave de transición
        document.documentElement.classList.add('theme-transitioning');
        applyTheme(nextTheme);
        setTimeout(() => {
            document.documentElement.classList.remove('theme-transitioning');
        }, 350);
    }

    // Inicialización inmediata al cargar el script para evitar parpadeos
    const initialTheme = getPreferredTheme();
    document.documentElement.dataset.theme = initialTheme;
    document.documentElement.setAttribute('data-theme', initialTheme);
    document.documentElement.setAttribute('data-admin-theme', initialTheme);

    // Enlazar eventos cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', function () {
        applyTheme(initialTheme);

        // Capturar clics en botones de tema personalizados y nativos de Django
        document.querySelectorAll('.theme-toggle-btn, .admin-theme-switch, .theme-toggle').forEach(btn => {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                toggleTheme();
            });
        });
    });

    // Exponer función global para toggling directo
    window.toggleAdminTheme = toggleTheme;
})();
