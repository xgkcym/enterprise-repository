# Python=3.11 pip=26.1.0



docker run -d --name es -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:8.12.0
curl -X POST "http://localhost:9200/_license/start_trial?acknowledge=true" -u elastic:你的密码
docker exec -it elasticsearch /bin/bash
./bin/elasticsearch-plugin install https://get.infini.cloud/elasticsearch/analysis-ik/8.12.0
./bin/elasticsearch-plugin list
docker restart elasticsearch

Query Routing（是否用RAG / 是否走WebSearch）