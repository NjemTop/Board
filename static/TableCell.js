export default {
    template: `
      <td>
        <span v-if="isSLAColumn" :title="getSLADescription(row.sla)">{{ value }}</span>
        <span v-else>{{ value }}</span>
      </td>
    `,
    props: {
      row: Object,
      column: Object,
      value: [String, Number, Boolean],
      getSLADescription: Function,
    },
    computed: {
      isSLAColumn() {
        return this.column.field === 'sla';
      },
    },
  };
  