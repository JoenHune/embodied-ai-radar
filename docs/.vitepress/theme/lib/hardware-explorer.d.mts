export type Match = { device_id:string;group:string;context_only:boolean;simulation:boolean;negation:boolean;usage_verified:boolean;locators:string[] }
export type Citation = { count:number;snapshot_date:string;source_name:string;source_url:string;snapshot_basis:string;queried_at:string|null }
export type Work = { id:string;title:string;date:string|null;date_precision:string|null;month:string|null;citation:Citation|null;source_url:string;process_state:string;source_state:string;matches:Match[] }
export type Device = { id:string;name:string;group:string;category:string;subcategory:string|null;aliases:string[];identity_level:string;work_count:number }
export type Data = { schema_version:string;records_sha256:string;catalog_hash:string;data_through:string;catalog_total:number;arxiv_catalog_total:number;catalog_months:Record<string,number>;catalog_unknown_month:number;categories:{id:string;name:string;categories:string[]}[];devices:Device[];rows:Work[];citation_coverage:{available:number;total:number;snapshot_dates:string[];actual_query_time_available:boolean};unknown_month_count:number;usage_verified_count:number }
export type Filters = {categories:string[];devices:string[];evidence:string;from:string;to:string;query:string}
export type Point = {period:string;count:number;analyzed:number;catalog:number;share:number|null;coverage:number|null}
export function emptyFilters():Filters
export function normalize(value:unknown):string
export function deviceSearch(device:Device,query:string):boolean
export function evidenceMatch(match:Match,evidence:string):boolean
export function matchingMentions(row:Work,filters:Filters):Match[]
export function filterRows(rows:Work[],filters:Filters):Work[]
export function sortRows(rows:Work[],order:string):Work[]
export function periodOf(month:string,granularity:string):string
export function trendSeries(data:Data,filters:Filters,granularity?:string):Point[]
export function growthRanking(data:Data,filters:Filters,granularity?:string,minimum?:number):{periods:string[];rows:{id:string;previous:number;count:number;growth:number|null}[];reason:string}
