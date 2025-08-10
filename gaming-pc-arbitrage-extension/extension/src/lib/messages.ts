/**
 * Type-safe message passing system for Chrome Extension
 */

import { z } from 'zod';
import type { Listing, Deal, ExtensionSettings } from '@arbitrage/core';

// Message types
export const MessageTypeSchema = z.enum([
  'PARSE_LISTING',
  'LISTING_PARSED',
  'CALCULATE_FMV',
  'FMV_CALCULATED',
  'SAVE_DEAL',
  'DEAL_SAVED',
  'GET_SETTINGS',
  'SETTINGS_RETRIEVED',
  'UPDATE_SETTINGS',
  'SETTINGS_UPDATED',
  'SHOW_NOTIFICATION',
  'TRACK_EVENT',
  'ERROR'
]);

export type MessageType = z.infer<typeof MessageTypeSchema>;

// Message payloads
export const ParseListingPayload = z.object({
  url: z.string(),
  platform: z.enum(['facebook', 'craigslist', 'offerup']),
  html: z.string()
});

export const ListingParsedPayload = z.object({
  listing: z.any(), // Would be Listing type
  success: z.boolean(),
  error: z.string().optional()
});

export const CalculateFMVPayload = z.object({
  listing: z.any()
});

export const FMVCalculatedPayload = z.object({
  fmv: z.number(),
  confidence: z.number(),
  breakdown: z.array(z.object({
    component: z.string(),
    value: z.number()
  }))
});

export const SaveDealPayload = z.object({
  listing: z.any(),
  fmv: z.number(),
  notes: z.string().optional()
});

export const NotificationPayload = z.object({
  title: z.string(),
  message: z.string(),
  type: z.enum(['success', 'info', 'warning', 'error']),
  dealId: z.string().optional()
});

export const EventPayload = z.object({
  name: z.string(),
  category: z.string(),
  properties: z.record(z.any()).optional()
});

// Message structure
export const MessageSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('PARSE_LISTING'),
    payload: ParseListingPayload
  }),
  z.object({
    type: z.literal('LISTING_PARSED'),
    payload: ListingParsedPayload
  }),
  z.object({
    type: z.literal('CALCULATE_FMV'),
    payload: CalculateFMVPayload
  }),
  z.object({
    type: z.literal('FMV_CALCULATED'),
    payload: FMVCalculatedPayload
  }),
  z.object({
    type: z.literal('SAVE_DEAL'),
    payload: SaveDealPayload
  }),
  z.object({
    type: z.literal('DEAL_SAVED'),
    payload: z.object({ dealId: z.string(), success: z.boolean() })
  }),
  z.object({
    type: z.literal('GET_SETTINGS'),
    payload: z.object({})
  }),
  z.object({
    type: z.literal('SETTINGS_RETRIEVED'),
    payload: z.object({ settings: z.any() })
  }),
  z.object({
    type: z.literal('UPDATE_SETTINGS'),
    payload: z.object({ settings: z.any() })
  }),
  z.object({
    type: z.literal('SETTINGS_UPDATED'),
    payload: z.object({ success: z.boolean() })
  }),
  z.object({
    type: z.literal('SHOW_NOTIFICATION'),
    payload: NotificationPayload
  }),
  z.object({
    type: z.literal('TRACK_EVENT'),
    payload: EventPayload
  }),
  z.object({
    type: z.literal('ERROR'),
    payload: z.object({ 
      message: z.string(),
      code: z.string().optional(),
      details: z.any().optional()
    })
  })
]);

export type Message = z.infer<typeof MessageSchema>;

// Message sender
export async function sendMessage<T extends Message>(
  message: T
): Promise<any> {
  try {
    const response = await chrome.runtime.sendMessage(message);
    return response;
  } catch (error) {
    console.error('Message sending failed:', error);
    throw error;
  }
}

// Tab message sender
export async function sendMessageToTab<T extends Message>(
  tabId: number,
  message: T
): Promise<any> {
  try {
    const response = await chrome.tabs.sendMessage(tabId, message);
    return response;
  } catch (error) {
    console.error('Tab message sending failed:', error);
    throw error;
  }
}

// Message listener helper
export function onMessage(
  handler: (
    message: Message,
    sender: chrome.runtime.MessageSender,
    sendResponse: (response?: any) => void
  ) => void | boolean | Promise<any>
) {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    try {
      const validatedMessage = MessageSchema.parse(message);
      const result = handler(validatedMessage, sender, sendResponse);
      
      // If handler returns a promise, handle it
      if (result instanceof Promise) {
        result.then(sendResponse).catch(error => {
          sendResponse({ success: false, error: error.message });
        });
        return true; // Keep channel open for async response
      }
      
      return result;
    } catch (error) {
      console.error('Invalid message received:', error);
      sendResponse({ success: false, error: 'Invalid message format' });
      return false;
    }
  });
}