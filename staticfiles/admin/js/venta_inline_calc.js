/**
 * Cálculo Dinámico e Interactivo de Subtotales y Totales para VentaAdmin
 * ======================================================================
 * Permite que al seleccionar un producto y cambiar la cantidad en el inline
 * de Django Admin, se calcule y muestre el subtotal en tiempo real junto con
 * el desglose tributario (Neto e IVA 19%) y el Gran Total.
 */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        const catalogEl = document.getElementById('productos-catalog-data');
        if (!catalogEl) return;

        let catalog = {};
        try {
            catalog = JSON.parse(catalogEl.textContent || '{}');
        } catch (e) {
            console.error('Error al analizar catálogo de productos:', e);
            return;
        }

        const inlineGroup = document.querySelector('.inline-group[id$="-group"]');
        if (!inlineGroup) return;

        // Crear contenedor para el resumen de cálculo en vivo
        const summaryCard = document.createElement('div');
        summaryCard.className = 'live-total-card';
        summaryCard.innerHTML = `
            <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(59, 130, 246, 0.08) 100%);
                        border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 16px 20px;
                        margin: 16px 0; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 15px;">
                <div>
                    <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #10b981; margin-bottom: 4px;">
                        ⚡ Cálculo Dinámico en Vivo (Detalles de Venta)
                    </div>
                    <div style="font-size: 13px; color: var(--adm-text-muted, #64748b);">
                        Total acumulado según los productos y cantidades seleccionadas:
                    </div>
                </div>
                <div style="display: flex; gap: 20px; align-items: center;">
                    <div style="text-align: right;">
                        <div style="font-size: 11px; color: var(--adm-text-muted, #64748b); text-transform: uppercase;">Neto (81%)</div>
                        <div id="live-neto-val" style="font-size: 15px; font-weight: 700; color: var(--adm-text, #0f172a);">$0 CLP</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 11px; color: #f59e0b; text-transform: uppercase;">IVA 19%</div>
                        <div id="live-iva-val" style="font-size: 15px; font-weight: 700; color: #f59e0b;">$0 CLP</div>
                    </div>
                    <div style="background: #10b981; color: #ffffff; padding: 8px 18px; border-radius: 10px; text-align: right; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);">
                        <div style="font-size: 11px; opacity: 0.9; text-transform: uppercase; font-weight: 600;">Total Venta</div>
                        <div id="live-total-val" style="font-size: 20px; font-weight: 800;">$0 CLP</div>
                    </div>
                </div>
            </div>
        `;

        inlineGroup.parentNode.insertBefore(summaryCard, inlineGroup);

        function formatCurrency(num) {
            return '$' + Math.round(num).toLocaleString('es-CL') + ' CLP';
        }

        function calculateLiveTotal() {
            let grandTotal = 0;
            const rows = inlineGroup.querySelectorAll('tr.form-row:not(.empty-form)');

            rows.forEach(row => {
                // Verificar si la fila está marcada para eliminación
                const deleteInput = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
                if (deleteInput && deleteInput.checked) return;

                const productSelect = row.querySelector('select[name$="-producto"]');
                const quantityInput = row.querySelector('input[name$="-cantidad"]');
                const subtotalCell = row.querySelector('.field-subtotal_display p, .field-subtotal_display');

                if (productSelect && quantityInput) {
                    const productId = productSelect.value;
                    const quantity = parseInt(quantityInput.value, 10) || 0;
                    const productInfo = catalog[productId];

                    let rowSubtotal = 0;
                    if (productInfo && quantity > 0) {
                        rowSubtotal = productInfo.precio * quantity;
                        grandTotal += rowSubtotal;
                    }

                    if (subtotalCell) {
                        if (rowSubtotal > 0) {
                            subtotalCell.innerHTML = `<span style="font-weight: 700; color: #10b981; font-size: 13px;">${formatCurrency(rowSubtotal)}</span> <small style="color: #64748b;">($${productInfo.precio.toLocaleString('es-CL')} c/u)</small>`;
                        } else {
                            subtotalCell.innerHTML = '<span style="color: #94a3b8; font-style: italic;">$0 CLP</span>';
                        }
                    }
                }
            });

            const neto = Math.round(grandTotal / 1.19);
            const iva = grandTotal - neto;

            const totalEl = document.getElementById('live-total-val');
            const netoEl = document.getElementById('live-neto-val');
            const ivaEl = document.getElementById('live-iva-val');

            if (totalEl) totalEl.textContent = formatCurrency(grandTotal);
            if (netoEl) netoEl.textContent = formatCurrency(neto);
            if (ivaEl) ivaEl.textContent = formatCurrency(iva);
        }

        // Escuchar eventos en los selectores de productos y cantidades
        inlineGroup.addEventListener('change', function (e) {
            if (e.target.matches('select[name$="-producto"], input[name$="-cantidad"], input[type="checkbox"][name$="-DELETE"]')) {
                calculateLiveTotal();
            }
        });

        inlineGroup.addEventListener('input', function (e) {
            if (e.target.matches('input[name$="-cantidad"]')) {
                calculateLiveTotal();
            }
        });

        // Escuchar cuando Django agrega una fila en el formset
        document.addEventListener('formset:added', function () {
            calculateLiveTotal();
        });
        document.addEventListener('formset:removed', function () {
            calculateLiveTotal();
        });

        // Cálculo inicial
        calculateLiveTotal();
    });
})();
