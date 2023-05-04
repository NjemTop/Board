export default {
    template: `
      <td>
        <span v-if="isSLAColumn" :title="$scopedSlots.getSLADescription({ row })">{{ value }}</span>
        <span v-else>{{ value }}</span>
      </td>
    `,
    props: {
      row: Object,
      column: Object,
      value: [String, Number, Boolean],
    },
    computed: {
      isSLAColumn() {
        return this.column.field === 'sla';
      },
    },
  };
  