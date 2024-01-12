async function poapList(path) {
  const template = await loadTemplateAsync(path)
  const nostr = window.NostrTools

  const defaultRelays = [
    'wss://relay.damus.io',
    'wss://relay.snort.social',
    'wss://nos.lol',
    'wss://nostr.band',
    'wss://nostr-pub.wellorder.net'
  ]

  Vue.component('poap-list', {
    name: 'poap-list',
    props: ['poaps', 'pubkey'],
    template,

    data: function () {
      return {
        page: 1,
        currentPage: 1,
        nextPage: null,
        totalPerPage: 10,
        perPage: ['10', '25', '50', '100']
      }
    },
    computed: {
      getData() {
        return this.poaps.slice(
          (this.page - 1) * this.totalPerPage,
          this.page * this.totalPerPage
        )
      }
    },
    methods: {
      openPoapExternal(id) {
        const naddr = nostr.nip19.naddrEncode({
          pubkey: this.pubkey,
          kind: 30009,
          identifier: id,
          relays: []
        })
        window.open(`https://badges.page/a/${naddr}`, '_blank')
      },
      editPoap(poap) {
        this.$emit('edit-poap', poap)
      }
    },
    created() {}
  })
}
