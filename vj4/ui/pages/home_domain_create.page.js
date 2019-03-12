import { NamedPage } from 'vj/misc/PageLoader';

const page = new NamedPage('home_domain_create', async () => {
  $(document).on('click', '#home-domain-create--generate-id', (ev) => {
    $('.section__body form [name="id"]').val(`r${1003 + Math.floor(Math.random() * 199810140309) % 260817}`);
  });
});

export default page;
