/**
 * Type-safe Message Bus for Chrome Extension
 * Uses discriminated unions and Zod validation
 */

import { z } from 'zod';
import type { 
  Listing, 
  Settings, 
  FMVResult, 
  ROIResult,
  RiskAssessment,
  Deal
} from '@/core';

// Message type discriminators
export const MessageType = {
  PARSE_PAGE: 'PARSE_PAGE',
  CALC_VALUATION: 'CALC_VALUATION',
  SAVE_LISTING: 'SAVE_LISTING',
  CREATE_DEAL: 'CREATE_DEAL',
  UPDATE_DEAL_STAGE: 'UPDATE_DEAL_STAGE',
  SCHEDULE_FOLLOWUP: 'SCHEDULE_FOLLOWUP',
  EXPORT_CSV: 'EXPORT_CSV',
  IMPORT_JSON: 'IMPORT_JSON',
  GET_SETTINGS: 'GET_SETTINGS',
  SET_SETTINGS: 'SET_SETTINGS',
  REQUEST_PERMISSION: 'REQUEST_PERMISSION',
  OPEN_DASHBOARD: 'OPEN_DASHBOARD',
  GENERATE_DRAFT: 'GENERATE_DRAFT',
  // Google Sheets
  SHEETS_AUTH: 'SHEETS_AUTH',
  SHEETS_SYNC: 'SHEETS_SYNC',
  SHEETS_PUSH_NOW: 'SHEETS_PUSH_NOW',
  SHEETS_PULL_NOW: 'SHEETS_PULL_NOW',
} as const;

// Request schemas
export const ParsePageRequestSchema = z.object({
  type: z.literal(MessageType.PARSE_PAGE),
  url: z.string().url(),
  html: z.string(),
  platform: z.enum(['facebook', 'craigslist', 'offerup']),
});

export const CalcValuationRequestSchema = z.object({
  type: z.literal(MessageType.CALC_VALUATION),
  listing: z.any(), // Should be Listing type but Zod doesn't know our custom types
});

export const SaveListingRequestSchema = z.object({
  type: z.literal(MessageType.SAVE_LISTING),
  listing: z.any(),
  autoCreateDeal: z.boolean().optional(),
});

export const CreateDealRequestSchema = z.object({
  type: z.literal(MessageType.CREATE_DEAL),
  listingId: z.string(),
  initialOffer: z.number().optional(),
});

export const UpdateDealStageRequestSchema = z.object({
  type: z.literal(MessageType.UPDATE_DEAL_STAGE),
  dealId: z.string(),
  stage: z.string(),
  reason: z.string().optional(),
});

export const ScheduleFollowupRequestSchema = z.object({
  type: z.literal(MessageType.SCHEDULE_FOLLOWUP),
  dealId: z.string(),
  scheduleFor: z.string().datetime(),
  message: z.string().optional(),
});

export const ExportCsvRequestSchema = z.object({
  type: z.literal(MessageType.EXPORT_CSV),
  dataType: z.enum(['deals', 'listings', 'analytics', 'inventory']),
  filters: z.record(z.any()).optional(),
});

export const ImportJsonRequestSchema = z.object({
  type: z.literal(MessageType.IMPORT_JSON),
  jsonData: z.string(),
});

export const GetSettingsRequestSchema = z.object({
  type: z.literal(MessageType.GET_SETTINGS),
});

export const SetSettingsRequestSchema = z.object({
  type: z.literal(MessageType.SET_SETTINGS),
  settings: z.any(),
  partial: z.boolean().optional(),
});

export const RequestPermissionSchema = z.object({
  type: z.literal(MessageType.REQUEST_PERMISSION),
  permission: z.string(),
});

export const OpenDashboardRequestSchema = z.object({
  type: z.literal(MessageType.OPEN_DASHBOARD),
  page: z.enum(['pipeline', 'analytics', 'settings']).optional(),
  dealId: z.string().optional(),
});

export const GenerateDraftRequestSchema = z.object({
  type: z.literal(MessageType.GENERATE_DRAFT),
  dealId: z.string(),
  templateId: z.string().optional(),
  variables: z.record(z.string()).optional(),
});

// Google Sheets request schemas
export const SheetsAuthRequestSchema = z.object({
  type: z.literal(MessageType.SHEETS_AUTH),
  action: z.enum(['connect', 'disconnect']),
});

export const SheetsSyncRequestSchema = z.object({
  type: z.literal(MessageType.SHEETS_SYNC),
  direction: z.enum(['push', 'pull', 'both']).optional(),
});

export const SheetsPushNowRequestSchema = z.object({
  type: z.literal(MessageType.SHEETS_PUSH_NOW),
});

export const SheetsPullNowRequestSchema = z.object({
  type: z.literal(MessageType.SHEETS_PULL_NOW),
});

// Union of all request types
export const MessageRequestSchema = z.discriminatedUnion('type', [
  ParsePageRequestSchema,
  CalcValuationRequestSchema,
  SaveListingRequestSchema,
  CreateDealRequestSchema,
  UpdateDealStageRequestSchema,
  ScheduleFollowupRequestSchema,
  ExportCsvRequestSchema,
  ImportJsonRequestSchema,
  GetSettingsRequestSchema,
  SetSettingsRequestSchema,
  RequestPermissionSchema,
  OpenDashboardRequestSchema,
  GenerateDraftRequestSchema,
  SheetsAuthRequestSchema,
  SheetsSyncRequestSchema,
  SheetsPushNowRequestSchema,
  SheetsPullNowRequestSchema,
]);

// Response types
export interface BaseResponse {
  success: boolean;
  error?: string;
}

export interface ParsePageResponse extends BaseResponse {
  listing?: Listing;
  fmv?: FMVResult;
  roi?: ROIResult;
  risk?: RiskAssessment;
}

export interface CalcValuationResponse extends BaseResponse {
  fmv?: FMVResult;
  roi?: ROIResult;
  risk?: RiskAssessment;
}

export interface SaveListingResponse extends BaseResponse {
  listingId?: string;
  dealId?: string;
}

export interface CreateDealResponse extends BaseResponse {
  dealId?: string;
}

export interface ScheduleFollowupResponse extends BaseResponse {
  alarmName?: string;
}

export interface ExportCsvResponse extends BaseResponse {
  csv?: string;
  filename?: string;
}

export interface GetSettingsResponse extends BaseResponse {
  settings?: Settings;
}

export interface RequestPermissionResponse extends BaseResponse {
  granted?: boolean;
}

export interface GenerateDraftResponse extends BaseResponse {
  draft?: string;
  variables?: Record<string, string>;
}

// Type inference
export type MessageRequest = z.infer<typeof MessageRequestSchema>;
export type ParsePageRequest = z.infer<typeof ParsePageRequestSchema>;
export type CalcValuationRequest = z.infer<typeof CalcValuationRequestSchema>;
export type SaveListingRequest = z.infer<typeof SaveListingRequestSchema>;
export type CreateDealRequest = z.infer<typeof CreateDealRequestSchema>;
export type UpdateDealStageRequest = z.infer<typeof UpdateDealStageRequestSchema>;
export type ScheduleFollowupRequest = z.infer<typeof ScheduleFollowupRequestSchema>;
export type ExportCsvRequest = z.infer<typeof ExportCsvRequestSchema>;
export type ImportJsonRequest = z.infer<typeof ImportJsonRequestSchema>;
export type GetSettingsRequest = z.infer<typeof GetSettingsRequestSchema>;
export type SetSettingsRequest = z.infer<typeof SetSettingsRequestSchema>;
export type RequestPermissionRequest = z.infer<typeof RequestPermissionSchema>;
export type OpenDashboardRequest = z.infer<typeof OpenDashboardRequestSchema>;
export type GenerateDraftRequest = z.infer<typeof GenerateDraftRequestSchema>;

// Response map type
export type MessageResponse<T extends MessageRequest> = 
  T extends ParsePageRequest ? ParsePageResponse :
  T extends CalcValuationRequest ? CalcValuationResponse :
  T extends SaveListingRequest ? SaveListingResponse :
  T extends CreateDealRequest ? CreateDealResponse :
  T extends ScheduleFollowupRequest ? ScheduleFollowupResponse :
  T extends ExportCsvRequest ? ExportCsvResponse :
  T extends GetSettingsRequest ? GetSettingsResponse :
  T extends RequestPermissionRequest ? RequestPermissionResponse :
  T extends GenerateDraftRequest ? GenerateDraftResponse :
  BaseResponse;

// Message sending helper with type safety
export async function sendMessage<T extends MessageRequest>(
  request: T
): Promise<MessageResponse<T>> {
  try {
    // Validate request
    const validated = MessageRequestSchema.parse(request);
    
    // Send to background script
    const response = await chrome.runtime.sendMessage(validated);
    
    // Type assertion based on discriminated union
    return response as MessageResponse<T>;
  } catch (error) {
    console.error('Message validation/send error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    } as MessageResponse<T>;
  }
}

// Message listener helper for background script
export function onMessage(
  handler: (
    request: MessageRequest,
    sender: chrome.runtime.MessageSender
  ) => Promise<BaseResponse> | BaseResponse
): void {
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    // Validate incoming message
    const validation = MessageRequestSchema.safeParse(request);
    
    if (!validation.success) {
      sendResponse({
        success: false,
        error: `Invalid message format: ${validation.error.message}`,
      });
      return true;
    }

    // Handle message
    Promise.resolve(handler(validation.data, sender))
      .then(sendResponse)
      .catch(error => {
        sendResponse({
          success: false,
          error: error.message || 'Handler error',
        });
      });

    return true; // Keep channel open for async response
  });
}

// Utility to check if we're in a content script context
export function isContentScript(): boolean {
  return !chrome.runtime.getBackgroundPage;
}

// Utility to check if we have permission for a host
export async function hasHostPermission(url: string): Promise<boolean> {
  try {
    const hasPermission = await chrome.permissions.contains({
      origins: [new URL(url).origin + '/*'],
    });
    return hasPermission;
  } catch {
    return false;
  }
}