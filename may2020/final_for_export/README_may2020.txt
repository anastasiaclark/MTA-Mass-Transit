NYC Mass Transit Spatial Layers
Notes for the May 2020 Edition
Frank Donnelly, Geospatial Data Librarian
GIS Lab, Baruch CUNY

Data for the NYC Mass Transit Spatial Layers series is generated from the static data developer feeds published by the MTA. The layers released for the May 2020 edition of our series represent reduced, essential service due to the COVID-19 pandemic. Compared to the previous edition that we published in December 2019, 40 bus routes were eliminated, most of them in Staten Island. The following 40 local and express bus routes that appeared in dec2019 were not present in may2020:

BX20, M98, Q26, S42, S66, S81, S84, S86, S90, S91, S92, S93, S94, S96, S98, SIM1, SIM10, SIM11, SIM15, SIM2, SIM22, SIM25, SIM26, SIM3, SIM30, SIM31, SIM32, SIM33, SIM34, SIM35, SIM4, SIM4X, SIM5, SIM6, SIM7, SIM8, SIM8X, SIM9, X37, X38.

One local route was present in may2020 that did not exist in dec2019: M191.

As a result, there was also a decrease in the number of bus stops. Some routes operated by private companies that contract with the MTA (for example SIM23 and SIM24) continue to operate, but these routes are never captured in the source data as the MTA does not own and operate them.

Reduced service for the NYC Subway was not reflected in the data feeds, so the GIS Lab created these layers manually by modifying the subway routes and stops layers we published in May 2019. The following subway routes were not operating in May 2020 and were removed: B, W, Z, and S shuttle from Times Square to Grand Central Station. In addition, the A and 5 trains eliminated service on certain branches. We also modified the group field, which is used for styling the routes with their trunk color, by removing the closed services.

We added a field named COVID_CHG to the subway stops layer that indicates which trains were removed or added for these stops, prefaced with a minus or plus sign, and modified the trains field accordingly to indicate the trains that stop there. There were 110 stops where service was impacted: 110 stops lost a train service, and 4 gained a service. The two stops for the shuttle to Times Square and Grand Central (S train) are closed and have no train service; we kept the stops in the dataset, added CLOSED to the stop name, and removed the train designation from the trains field.

We did not publish updates for the Metro North or LIRR for this edition, because there had been no changes in the underlying source data.

