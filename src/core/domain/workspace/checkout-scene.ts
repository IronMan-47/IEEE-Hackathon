import { WorkspaceState } from './types';

/**
 * Deterministic E-commerce Checkout Initial Workspace Scene
 * Contains intentionally unoptimized layout and styling to test AI proposals.
 */
export function createCheckoutInitialScene(): WorkspaceState {
  return {
    revision: 1,
    title: 'E-commerce Checkout Screen',
    lastUpdated: Date.now(),
    elements: {
      'card_main': {
        id: 'card_main',
        type: 'container',
        x: 20,
        y: 20,
        w: 360,
        h: 460,
        style: {
          fill: '#1E293B',
          borderRadius: 12,
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1
        }
      },
      'txt_header': {
        id: 'txt_header',
        type: 'heading',
        x: 40,
        y: 40,
        w: 320,
        h: 30,
        label: 'Checkout & Review',
        parentId: 'card_main',
        style: {
          color: '#F8FAFC',
          fontSize: 20,
          fontWeight: 700
        }
      },
      'card_summary': {
        id: 'card_summary',
        type: 'card',
        x: 40,
        y: 85,
        w: 320,
        h: 80,
        parentId: 'card_main',
        style: {
          fill: 'rgba(255, 255, 255, 0.05)',
          borderRadius: 8,
          borderColor: 'rgba(255, 255, 255, 0.08)',
          borderWidth: 1
        }
      },
      'txt_item_name': {
        id: 'txt_item_name',
        type: 'text',
        x: 55,
        y: 105,
        w: 180,
        h: 20,
        label: 'Pro Plan Subscription',
        parentId: 'card_summary',
        style: {
          color: '#CBD5E1',
          fontSize: 14,
          fontWeight: 500
        }
      },
      'txt_item_price': {
        id: 'txt_item_price',
        type: 'text',
        x: 270,
        y: 105,
        w: 80,
        h: 20,
        label: '₹999',
        parentId: 'card_summary',
        style: {
          color: '#06B6D4',
          fontSize: 16,
          fontWeight: 700
        }
      },
      'inp_coupon': {
        id: 'inp_coupon',
        type: 'input',
        x: 40,
        y: 185,
        w: 200,
        h: 40,
        label: 'PROMO2026',
        parentId: 'card_main',
        style: {
          fill: '#0F172A',
          color: '#94A3B8',
          borderRadius: 6,
          borderColor: '#334155',
          borderWidth: 1,
          fontSize: 13
        }
      },
      'btn_coupon': {
        id: 'btn_coupon',
        type: 'button',
        x: 250,
        y: 185,
        w: 110,
        h: 40,
        label: 'Apply Code',
        parentId: 'card_main',
        style: {
          fill: '#2563EB',
          color: '#FFFFFF',
          borderRadius: 6,
          fontSize: 13,
          fontWeight: 600
        }
      },
      'btn_pay': {
        id: 'btn_pay',
        type: 'button',
        x: 40,
        y: 250,
        w: 180,
        h: 36,
        label: 'Pay Now (₹999)',
        parentId: 'card_main',
        style: {
          fill: '#475569',
          color: '#CBD5E1',
          borderRadius: 6,
          fontSize: 13,
          fontWeight: 400
        }
      }
    }
  };
}
