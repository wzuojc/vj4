import { NamedPage } from 'vj/misc/PageLoader';

const page = new NamedPage('home_domain', async () => {
  $(document).on('click', '#home-domain--join-domain', (ev) => {
    let id = $('[name="home-domain--join-domain-id"]').val();
    id = id.trim();
    if (id.length < 4) {
      return;
    }
    window.location.href = `/d/${id}/join`;
  });
});

export default page;
