# Python=3.11 pip=26.1.0



docker run -d --name es -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:8.12.0
curl -X POST "http://localhost:9200/_license/start_trial?acknowledge=true" -u elastic:你的密码
docker exec -it elasticsearch /bin/bash
./bin/elasticsearch-plugin install https://get.infini.cloud/elasticsearch/analysis-ik/8.12.0
./bin/elasticsearch-plugin list
docker restart elasticsearch

Query Routing（是否用RAG / 是否走WebSearch）


docker run -d --name milvus --restart=unless-stopped -p 19530:19530 -p 9091:9091 -v milvus_data:/var/lib/milvus milvusdb/milvus:v2.6.13

## Tests

Run the `preferred_topics` backend unit tests locally:

```bash
python -m unittest tests.test_preferred_topics
```
