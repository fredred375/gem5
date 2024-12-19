/**
 * @file
 * Stride Prefetcher template instantiations.
 */

#include "mem/cache/prefetch/ideal.hh"

#include <algorithm>
#include <fstream>
#include <iostream>

#include "debug/ECE498RK.hh"
#include "ideal.hh"
#include "params/IdealPrefetcher.hh"
#include "sim/system.hh"

namespace gem5
{

  namespace prefetch
  {

    void
    Ideal::PriorityPacket::createPkt(Addr paddr, unsigned blk_size,
                                     RequestorID requestor_id,
                                     Tick t)
    {
      /* Create a prefetch memory request */
      RequestPtr req = std::make_shared<Request>(paddr, blk_size,
                                                 0, requestor_id);
      req->setContext(0);
      req->taskId(context_switch_task_id::Prefetcher);
      pkt = new Packet(req, MemCmd::HardPFReq);
      pkt->allocate();
      tick = t;
    }

    Ideal::Ideal(const IdealPrefetcherParams &p)
        : Base(p),
          distance(p.distance)
    {
      initializePredictions(p.prediction_file);
    }

    Ideal::~Ideal()
    {
      // Delete the queued prefetch packets
      while (!pfq.empty())
      {
        auto p = pfq.top();
        delete p.pkt;
        pfq.pop();
      }
    }

    void Ideal::notify(const CacheAccessProbeArg &acc, const PrefetchInfo &pfi)
    {
      Addr blk_addr = blockAddress(pfi.getAddr());
      // push notifyIndex + distance prediction on the queue
      while (notifyIndex + distance + hitCount < predictions.size())
      {
        Tick prefetch_tick = curTick();
        PriorityPacket dpp(0, priority_counter--);
        dpp.createPkt(predictions[notifyIndex + distance + hitCount].addr,
                      blkSize, requestorId, prefetch_tick);
        pfq.push(dpp);
        DPRINTF(ECE498RK, "Ideal prefetching address: %x, tick: %lu\n",
                predictions[notifyIndex + distance + hitCount].addr,
                prefetch_tick);
        if (predictions[notifyIndex + hitCount].miss)
          break;
        else
          hitCount++;
      }

      DPRINTF(ECE498RK, "Ideal prefetcher notify packet index: %lu\n",
              this->notifyIndex + hitCount);
      if (notifyIndex < predictions.size())
      {
        DPRINTF(ECE498RK,
                "Ideal prefetcher notify packet addr: %x, tick: %lu\n",
                predictions[notifyIndex + hitCount].addr,
                predictions[notifyIndex + hitCount].time);
      }
      if (blk_addr == blockAddress(predictions[notifyIndex + hitCount].addr))
      {
        notifyIndex++;
      }
    }

    PacketPtr Ideal::getPacket()
    {
      if (pfq.empty())
      {
        return nullptr;
      }

      PacketPtr pkt = pfq.top().pkt;
      pfq.pop();

      prefetchStats.pfIssued++;
      issuedPrefetches += 1;
      assert(pkt != nullptr);
      return pkt;
    }

    Tick Ideal::nextPrefetchReadyTime() const
    {
      return pfq.empty() ? MaxTick : pfq.top().tick;
    }

    void Ideal::initializePredictions(const std::string &prediction_file)
    {
      // read prediction file
      std::ifstream file(prediction_file);
      if (!file.is_open())
      {
        std::cerr << "Failed to open prediction file: "
                  << prediction_file << std::endl;
        return;
      }

      DPRINTF(ECE498RK, "Prefetch distance: %d\n", distance);

      std::string line;
      while (std::getline(file, line))
      {
        Tick prediction_tick;
        Addr prediction_addr;
        PacketId packet_id;
        std::string caller_name = "";
        std::string status = "";
        std::istringstream iss(line);
        // line is in form
        // 2000: system.l2cache: access miss for ReadSharedReq [28540:2857f] IF

        iss >> prediction_tick;
        iss.ignore(1);        // ignore the colon and space
        iss.ignore(256, ':'); // ignore everything until the ':'
        iss.ignore(1);        // ignore the space
        iss.ignore(256, ' '); // ignore everything until space
        iss >> status;
        iss.ignore(1);        // ignore the space
        iss.ignore(256, ' '); // ignore everything until space
        iss >> caller_name;
        iss.ignore(256, '['); // ignore everything until the '['
        iss >> std::hex >> prediction_addr;

        if (caller_name == "CleanEvict" ||
            caller_name.compare(0, 9, "Writeback") == 0)
        {
          continue;
        }

        predictions.push_back({prediction_tick, prediction_addr,
                               status == "miss"});
      }
      file.close();
      // push distance amout of prefetches
      for (size_t i = 0; i < distance && i < predictions.size(); i++)
      {
        Tick prefetch_tick = curTick();
        PriorityPacket dpp(0, priority_counter--);
        dpp.createPkt(predictions[i].addr, blkSize,
                      requestorId, prefetch_tick);
        pfq.push(dpp);
        DPRINTF(ECE498RK, "Prefetching address: %x, tick: %lu\n",
                predictions[i].addr, prefetch_tick);
      }
      DPRINTF(ECE498RK, "Issued a total of %lu predictions\n",
              predictions.size());
    }

  } // namespace prefetch
} // namespace gem5
