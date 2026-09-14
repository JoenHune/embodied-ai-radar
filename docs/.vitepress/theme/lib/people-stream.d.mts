export const PEOPLE_BATCH_SIZE: number
export function nextPeopleCount(current: number, total: number): number
export function peopleStreamKey(state: { q: string; direction: string; lens: string; sort: string }): string
export function preservePeoplePage(router: { onBeforePageLoad?: (href: string) => boolean | void | PromiseLike<boolean | void> }, pathname: string, restore?: () => void): () => void
export function observePeopleEnd(element: Element | null, canLoad: () => boolean, loadMore: () => void, Observer?: typeof IntersectionObserver | null): () => void
