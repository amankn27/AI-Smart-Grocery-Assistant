import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

// Running bill with INR subtotal, embedded GST, and grand total.
export function CartView() {
  const { data: cart } = useQuery({ queryKey: ["cart"], queryFn: api.getCart, refetchInterval: 3000 });

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <h2 className="mb-3 font-semibold">🧾 Cart</h2>
      {!cart || cart.items.length === 0 ? (
        <p className="text-sm text-slate-400">No items yet. Scan a product to add it.</p>
      ) : (
        <>
          <ul className="divide-y text-sm">
            {cart.items.map((i) => (
              <li key={i.product_id} className="flex justify-between py-2">
                <span>
                  {i.name} × {i.quantity}
                </span>
                <span>₹{i.line_total}</span>
              </li>
            ))}
          </ul>
          <div className="mt-3 space-y-1 border-t pt-2 text-sm">
            <Row label="Subtotal" value={cart.subtotal} />
            <Row label="GST (incl.)" value={cart.total_gst} />
            <div className="flex justify-between border-t pt-1 font-bold">
              <span>Total</span>
              <span>₹{cart.total}</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-slate-500">
      <span>{label}</span>
      <span>₹{value}</span>
    </div>
  );
}
