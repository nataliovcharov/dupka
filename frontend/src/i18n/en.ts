// english texts, mk.ts must have exactly the same keys
export const en = {
  header: {
    privacy: 'Privacy',
    language: 'Language',
  },
  map: {
    reportButton: 'Report damage',
    filterLabel: 'Show severity',
    loadFailed: "Couldn't load the reports on the map.",
  },
  severity: {
    high: 'High',
    medium: 'Medium',
    low: 'Low',
  },
  severityLong: {
    high: 'High severity',
    medium: 'Medium severity',
    low: 'Low severity',
  },
  damage: {
    D40: 'Pothole',
    D20: 'Alligator cracking',
    D10: 'Transverse crack',
    D00: 'Longitudinal crack',
    unknown: 'Road damage',
  },
  report: {
    title: 'Report road damage',
    photoAlt: 'Your photo of the damage',
    locating: 'Finding your location…',
    dragPin: 'Drag the pin if it is not exactly on the damage.',
    noLocation: 'We could not get your location. Move the pin to the damage.',
    outsideMacedonia: 'The location must be in North Macedonia.',
    cancel: 'Cancel',
    send: 'Send report',
    sending: 'Sending…',
    blurNote: 'Faces and number plates are blurred automatically.',
    privacyLink: 'How we use your photo',
    thanksTitle: 'Thank you!',
    thanksBody:
      "Your report was sent. We check every photo before it goes on the public map, usually within a minute. Until then, you'll see it as a red ring.",
    done: 'Done',
  },
  errors: {
    generic: 'Something went wrong. Please try again.',
    network: 'No connection. Check your internet and try again.',
    tooLarge: 'The photo is too large.',
    wrongType: 'Please choose a JPEG, PNG or WebP photo.',
    notAPhoto: "This file isn't a photo we can read.",
    tooMany: 'Too many reports from this device. Please try again later.',
  },
  details: {
    close: 'Close',
    loading: 'Loading…',
    loadFailed: "Couldn't load this report.",
    photoMissing: 'Photo not available',
    photoAlt: '{{title}}, photo {{number}} of {{count}}',
    previous: 'Previous photo',
    next: 'Next photo',
    reportedOnce: 'Reported {{date}}',
    reportedTimes_one: 'Reported {{count}} time, first on {{date}}',
    reportedTimes_other: 'Reported {{count}} times, first on {{date}}',
    thisPhoto: 'This photo: {{date}}',
  },
  privacy: {
    backToMap: 'Back to map',
    title: 'Privacy',
    updated: 'Last updated {{date}}',
    collectTitle: 'What we collect',
    collect1:
      "When you report road damage we keep the photo, the location you confirm on the map and the time. We don't ask for your name, email or an account.",
    collect2:
      'Photos from phones often carry hidden data, like where and with which camera they were taken. We remove all of it as soon as the photo arrives.',
    blurTitle: 'Faces and number plates',
    blur: 'Faces and number plates are found and blurred automatically before anyone else can see the photo. We only keep the blurred version. If blurring fails, the photo is never shown.',
    publicTitle: 'What is public',
    public:
      'Once a report is checked, the blurred photo, its location, the type of damage, how bad it is and the date appear on the public map. Reports of the same spot are shown together.',
    useTitle: 'How we use it',
    use1: 'To show road damage on the map.',
    use2: 'To improve the automatic damage detection. Photos and our review decisions are used to train and test the model.',
    use3: "Photos are checked on our own server. They are not sent to other companies for analysis, and we don't sell or share them.",
    technicalTitle: 'Technical data',
    technical:
      'To stop automated abuse, we count uploads per IP address for up to a day. The count is kept in memory only and is not stored with your report. Our hosting provider may keep standard server logs.',
    retentionTitle: 'How long we keep it',
    retention1: 'Public reports stay while the damage is on the map.',
    retention2: "Photos of reports we don't publish are deleted after 30 days.",
    contactTitle: 'Questions and removal',
    contact: 'Contact details for questions and removal requests will be added here before launch.',
  },
}

export type Messages = typeof en
